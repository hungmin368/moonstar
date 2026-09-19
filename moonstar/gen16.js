/* gen16.js — 大尺寸（N≥16）唯一解快速生成器（moonstar v1.7）
 *
 * 算法：兩階段批次殺解（two-phase batch-kill）
 *
 *   核心數學性質（已實測驗證）：
 *   (P1) 任一合法解中，星格 X 必是其所屬區域的唯一星 ⇒ 把 X 搬到相鄰區域
 *        即殺死所有「星在 X」的解（原區域少一星、新區域多一星，兩者皆違規）。
 *   (P2) 搬移只影響「星在 X」的解；X 非星的解完全不受影響。
 *        ⇒ 只要絕不搬動保留解 A 的星格，A 永遠存活（解數≥1 不變式）。
 *   (P3) 搬移可能創造新解（條件：星在 X 且原區域另有星且目標區域無星），
 *        但新解必須「星在被搬格」——把搬移目標偏向小區域可抑制創造。
 *
 *   流程：
 *   1. 隨機連通區域分割（區域數=N、每區≥2格，同引擎 randomRegions 語意）
 *   2. 位元遮罩 MRV 求解器枚舉至 K 上限（取樣）——解數≥K 時極快
 *   3. 取樣期：只搬「熱點格」（出現在 ≥ freqMin 個取樣解中），保持解數高位
 *      求解維持便宜；解數降到 <K 自動進入精確期
 *   4. 精確期：解數<K 時枚舉即完整清單 ⇒ 貪婪集合覆蓋挑最少格數殺光非 A 解
 *   5. 解數=1 且未觸節點上限 ＝ 完整枚舉證明唯一解 → 返回
 *
 *   超時/降級：restartCap 次重啟 + deadlineMs 硬限時 → 返回 {ok:false, reason}
 *   交由呼叫端降級（遊戲：顯示重試；離線池：跳過該盤）。
 *
 * 驗證責任：本模組以自身求解器完整枚舉證明唯一（!aborted 且解數=1 才返回）。
 * 引擎端另以既有 solve2（行序）獨立複核；測試端三求解器交叉＋手寫驗證器。
 *
 * 與引擎既有路徑完全獨立：僅提供 gen16* 命名空間函式，N=4~14 仍走原路徑。
 * 歷史教訓：簡易版 MRV（gen16SolveBasic）的候選陣列必須在遞迴前快照，
 * 否則遞迴覆寫共享 cand 會枚舉非法解——gen15b「N≥16 不可行」假象的根因。
 */
'use strict';

function gen16Rng(seed){ /* xorshift128：可重現隨機（測試用） */
  let a=(seed>>>0)||88675123, b=((seed>>>0)*2654435761)>>>0||362436069, c=521288629, d=88675123;
  return function(){
    const t=a^(a<<11); a=b; b=c; c=d;
    d=(d^(d>>>19))^(t^(t>>>8));
    return (d>>>0)/4294967296;
  };
}
function gen16Shuffle(arr, rng){
  for(let i=arr.length-1;i>0;i--){
    const j=Math.floor(rng()*(i+1));
    const t=arr[i]; arr[i]=arr[j]; arr[j]=t;
  }
  return arr;
}
function gen16Neighbors4(i, N){
  const r=Math.floor(i/N), c=i%N, out=[];
  if(r>0) out.push(i-N);
  if(r<N-1) out.push(i+N);
  if(c>0) out.push(i-1);
  if(c<N-1) out.push(i+1);
  return out;
}

/* 隨機連通區域分割（與引擎 randomRegions 同語意；獨立複製以保持模組自足） */
function gen16RandomRegions(N, rng){
  rng = rng || Math.random;
  const total=N*N;
  for(let t=0;t<200;t++){
    const regionOf=new Array(total).fill(-1);
    const seeds=gen16Shuffle([...Array(total).keys()], rng).slice(0,N);
    const frontiers=seeds.map(()=>[]);
    seeds.forEach((s,i)=>{ regionOf[s]=i; gen16Neighbors4(s,N).forEach(nb=>frontiers[i].push(nb)); });
    let assigned=N;
    while(assigned<total){
      let progressed=false;
      for(const r of gen16Shuffle([...Array(N).keys()], rng)){
        if(assigned>=total) break;
        let cell=null;
        while(frontiers[r].length){
          const pick=Math.floor(rng()*frontiers[r].length);
          const c=frontiers[r][pick];
          frontiers[r].splice(pick,1);
          if(regionOf[c]!==-1) continue;
          cell=c; break;
        }
        if(cell===null) continue;
        regionOf[cell]=r; assigned++; progressed=true;
        gen16Neighbors4(cell,N).forEach(nb=>{ if(regionOf[nb]===-1) frontiers[r].push(nb); });
      }
      if(!progressed) break;
    }
    if(assigned<total) continue;
    const sizes=new Array(N).fill(0);
    regionOf.forEach(r=>sizes[r]++);
    if(sizes.some(s=>s<2)) continue;
    return regionOf;
  }
  return null;
}

/* ---------- 求解器 ----------
 * gen16SolveMRV：位元遮罩＋增量傳播＋前瞻（每列候選遮罩；指派時傳播
 *   列/區/相鄰禁制；MRV 選最少候選列；某列候選=0 即剪枝）。
 *   回溯以逐層快照還原（不用逆向 |=：其不安全——先前已清空的位元會被錯誤點亮）。
 * gen16SolveBasic：修正版簡易 MRV（驗證用第二實作；候選快照見註解）。
 * 兩者返回 {sols, nodes, aborted}；aborted=false 且 sols.length<K 時為完整
 * 枚舉——sols.length===1 即唯一解的完整證明。 */

const GEN16_PC=(function(){ const t=new Uint8Array(1<<16); for(let i=1;i<(1<<16);i++) t[i]=t[i>>1]+(i&1); return t; })();
function gen16Popcount(x){ return x<65536?GEN16_PC[x]:(x=(x-(x>>1)&0x55555555),x=(x+(x>>2)&0x33333333),x=(x+(x>>4)&0x0f0f0f0f),(x*0x01010101)>>24); }

function gen16SolveMRV(N, regionOf, nodeLimit, K){
  const LIMIT=(nodeLimit===undefined||nodeLimit===null)?Infinity:nodeLimit;
  const MAXK=K||2;
  const FULL=(1<<N)-1;
  /* regCols[r][g]：列 r 中屬於區域 g 的欄位遮罩 */
  const regCols=[];
  for(let r=0;r<N;r++){
    const a=new Array(N).fill(0);
    for(let c=0;c<N;c++) a[regionOf[r*N+c]]|=1<<c;
    regCols.push(a);
  }
  const assigned=new Int32Array(N).fill(-1);
  const cand=new Int32Array(N).fill(FULL);
  const snapC=[]; for(let d=0;d<=N;d++) snapC.push(new Int32Array(N));
  let rows=[]; for(let r=0;r<N;r++) rows.push(r);
  const sols=[]; let nodes=0, aborted=false;
  (function bt(){
    if(++nodes>LIMIT){ aborted=true; return; }
    if(sols.length>=MAXK) return;
    if(rows.length===0){
      const s=new Array(N);
      for(let r=0;r<N;r++) s[r]=assigned[r];
      sols.push(s);
      return;
    }
    let best=-1, bestCnt=N+2;
    for(let i=0;i<rows.length;i++){
      const pc=gen16Popcount(cand[rows[i]]);
      if(pc===0) return;                 /* 前瞻：某列已無候選 → 剪枝 */
      if(pc<bestCnt){ bestCnt=pc; best=i; if(pc===1) break; }
    }
    const r0=rows[best], d=N-rows.length;
    snapC[d].set(cand);
    /* 子層列清單：slice+splice（不可原地換尾——兄弟候選間索引會失效） */
    const parentRows=rows;
    const childRows=parentRows.slice(); childRows.splice(best,1);
    let m=cand[r0];
    while(m){
      const bit=m&-m; m^=bit;
      const c=31-Math.clz32(bit);
      const g0=regionOf[r0*N+c];
      assigned[r0]=c;
      rows=childRows;
      for(let i=0;i<childRows.length;i++){
        const rr=childRows[i];
        cand[rr]&=~bit;
        cand[rr]&=~regCols[rr][g0];
        if(rr===r0-1||rr===r0+1) cand[rr]&=~((bit<<1)|(bit>>>1));
      }
      bt();
      rows=parentRows;
      assigned[r0]=-1;
      cand.set(snapC[d]);
      if(sols.length>=MAXK||aborted) return;
    }
  })();
  return {sols, nodes, aborted};
}

function gen16SolveBasic(N, regionOf, nodeLimit, K){
  const assigned=new Int32Array(N).fill(-1);
  let colMask=0, regMask=0, remaining=N, nodes=0, aborted=false;
  const LIMIT=(nodeLimit===undefined||nodeLimit===null)?Infinity:nodeLimit;
  const MAXK=K||2;
  const sols=[];
  const cand=new Array(N);
  function candidates(r){
    let n=0;
    const base=r*N;
    const below=r>0?assigned[r-1]:-9;
    const above=r<N-1?assigned[r+1]:-9;
    for(let c=0;c<N;c++){
      if(colMask>>c&1) continue;
      if(regMask>>regionOf[base+c]&1) continue;
      if(below>=0 && Math.abs(c-below)<=1) continue;
      if(above>=0 && Math.abs(c-above)<=1) continue;
      cand[n++]=c;
    }
    return n;
  }
  (function bt(){
    if(++nodes>LIMIT){ aborted=true; return; }
    if(sols.length>=MAXK) return;
    if(remaining===0){ sols.push(Array.from(assigned)); return; }
    let bestRow=-1, bestCnt=N+1;
    for(let r=0;r<N;r++){
      if(assigned[r]>=0) continue;
      const cnt=candidates(r);
      if(cnt===0) return;
      if(cnt<bestCnt){ bestCnt=cnt; bestRow=r; if(cnt===1) break; }
    }
    const r=bestRow, n=candidates(r);
    const local=cand.slice(0,n); /* 快照：防遞迴覆寫共享候選陣列 */
    for(let i=0;i<n;i++){
      const c=local[i];
      const reg=regionOf[r*N+c];
      assigned[r]=c; colMask|=1<<c; regMask|=1<<reg; remaining--;
      bt();
      assigned[r]=-1; colMask&=~(1<<c); regMask&=~(1<<reg); remaining++;
      if(sols.length>=MAXK||aborted) return;
    }
  })();
  return {sols, nodes, aborted};
}

/* 區域去掉 cellIdx 後是否仍連通（且剩≥2格） */
function gen16ConnectedWithout(cellsSet, X, N){
  const cells=[];
  for(const c of cellsSet) if(c!==X) cells.push(c);
  if(cells.length<2) return false;
  const inSet=new Set(cells);
  const seen=new Set([cells[0]]), st=[cells[0]];
  while(st.length){
    const cur=st.pop();
    for(const nb of gen16Neighbors4(cur,N)){
      if(inSet.has(nb)&&!seen.has(nb)){ seen.add(nb); st.push(nb); }
    }
  }
  return seen.size===cells.length;
}

/* ---------- 主生成器 ----------
 * 成功返回 {ok:true, regionOf, sol, stats}；失敗 {ok:false, reason, stats}
 * opts（全部可選）：deadlineMs, kSample, freqMin, coverCap, nodeLimit,
 *   batchCap, roundCap, restartCap, maxRegionSize, rng, log, onRound
 * 唯一解由內部完整枚舉證明（!aborted 且解數=1 才返回 ok）。 */
function gen16Generate(N, opts){
  opts=opts||{};
  const rng=opts.rng||Math.random;
  const K=opts.kSample||64;
  const freqMin=opts.freqMin||Math.max(3,Math.floor(K/4));
  const coverCap=opts.coverCap||24;
  const NL=(opts.nodeLimit!==undefined)?opts.nodeLimit:20000000;
  const batchCap=opts.batchCap||0;
  const roundCap=opts.roundCap||300;
  const restartCap=opts.restartCap||30;
  const maxRegionSize=opts.maxRegionSize||0;
  const deadline=opts.deadlineMs||10000;
  const log=opts.log||null;
  const onRound=opts.onRound||null;
  const hasPerf=(typeof performance!=='undefined'&&performance.now);
  const now=hasPerf?()=>performance.now():()=>Date.now();
  const t0=now();
  const stats={restarts:0, rounds:0, moves:0, solves:0, nodes:0, solveMs:0, creations:0};
  function fail(reason){ stats.t=now()-t0; return {ok:false, reason, stats}; }
  function solveOnce(){
    const ts=now();
    const r=gen16SolveMRV(N, regionOf, NL, K);
    stats.solves++; stats.nodes+=r.nodes; stats.solveMs+=now()-ts;
    return r;
  }
  let regionOf=null;

  for(let restart=0;restart<restartCap;restart++){
    if(now()-t0>deadline) return fail('deadline');
    stats.restarts++;
    regionOf=gen16RandomRegions(N, rng);
    if(!regionOf) continue;
    const regCells=[];
    for(let g=0;g<N;g++) regCells.push(new Set());
    for(let i=0;i<N*N;i++) regCells[regionOf[i]].add(i);

    let res=solveOnce();
    if(res.aborted) continue;
    if(res.sols.length===0) continue;
    if(res.sols.length===1){ stats.t=now()-t0; return {ok:true, regionOf, sol:res.sols[0], stats}; }

    for(let round=0;round<roundCap;round++){
      if((round&3)===0 && now()-t0>deadline) return fail('deadline');
      stats.rounds++;
      const sols=res.sols;
      const sampled=sols.length>=K;
      const A=sols[0];
      const protect=new Set();
      for(let r=0;r<N;r++) protect.add(r*N+A[r]);
      const prevCount=sampled?null:sols.length;

      /* 選搬移格：取樣期=熱點格；精確期=貪婪集合覆蓋 */
      const batch=[];
      if(sampled){
        const freq=new Map();
        for(let s=1;s<sols.length;s++)
          for(let r=0;r<N;r++){
            const cell=r*N+sols[s][r];
            if(!protect.has(cell)) freq.set(cell,(freq.get(cell)||0)+1);
          }
        const hot=[];
        for(const [cell,f] of freq) if(f>=freqMin) hot.push([cell,f]);
        hot.sort((a,b)=>b[1]-a[1]);
        for(const [cell] of hot) batch.push(cell);
        if(!batch.length){                 /* 無格過門檻 → 至少搬最高頻格保證進展 */
          let top=null, tf=-1;
          for(const [cell,f] of freq) if(f>tf){ tf=f; top=cell; }
          if(top!==null) batch.push(top);
        }
      } else {
        const cnt=sols.length;
        const coverMap=new Map();          /* cell -> 覆蓋的解索引 */
        for(let s=1;s<cnt;s++)
          for(let r=0;r<N;r++){
            const cell=r*N+sols[s][r];
            if(protect.has(cell)) continue;
            let a=coverMap.get(cell);
            if(!a){ a=[]; coverMap.set(cell,a); }
            a.push(s);
          }
        const uncovered=new Set();
        for(let s=1;s<cnt;s++) uncovered.add(s);
        while(uncovered.size && batch.length<coverCap){
          let bestCell=-1, bestGain=0;
          for(const [cell,arr] of coverMap){
            let g=0;
            for(const s of arr) if(uncovered.has(s)) g++;
            if(g>bestGain){ bestGain=g; bestCell=cell; }
          }
          if(bestCell<0) break;            /* 其餘解的差異格皆不可用 */
          batch.push(bestCell);
          for(const s of coverMap.get(bestCell)) uncovered.delete(s);
        }
      }
      if(batchCap>0 && batch.length>batchCap) batch.length=batchCap;
      if(!batch.length) break;             /* 無可搬格 → 換盤 */

      /* 執行搬移：目標=最小相鄰區域（抑制新解創造＋區域平衡） */
      let moved=0;
      for(const X of batch){
        const R=regionOf[X];
        if(regCells[R].size<3) continue;
        if(!gen16ConnectedWithout(regCells[R], X, N)) continue;
        const targets=[];
        for(const nb of gen16Neighbors4(X,N)){
          const t=regionOf[nb];
          if(t!==R && targets.indexOf(t)<0) targets.push(t);
        }
        if(!targets.length) continue;
        let T=targets[0];
        for(let i=1;i<targets.length;i++) if(regCells[targets[i]].size<regCells[T].size) T=targets[i];
        if(maxRegionSize>0 && regCells[T].size>=maxRegionSize) continue;
        regCells[R].delete(X); regCells[T].add(X); regionOf[X]=T;
        moved++;
      }
      if(moved===0) break;                 /* 本盤無可搬格 → 換盤 */
      stats.moves+=moved;

      const before=sampled?'K':sols.length;
      const nodesBefore=stats.nodes;
      res=solveOnce();
      if(res.aborted) break;               /* 樹太大 → 換盤 */
      if(res.sols.length===0) break;       /* 理論不可達（A 必存活）；防禦換盤 */
      if(!sampled && res.sols.length>prevCount) stats.creations += res.sols.length - prevCount;
      if(onRound) onRound({round, mode:sampled?'sampled':'exact', before, after:res.sols.length>=K?'K':res.sols.length, moved, nodes:stats.nodes-nodesBefore, creations:res.sols.length>prevCount&&!sampled?(res.sols.length-prevCount):0});
      if(res.sols.length===1){
        stats.t=now()-t0;
        if(log) log(`N=${N} done: restart=${stats.restarts} rounds=${stats.rounds} moves=${stats.moves} nodes=${stats.nodes} t=${(stats.t/1000).toFixed(2)}s`);
        return {ok:true, regionOf, sol:res.sols[0], stats};
      }
    }
  }
  return fail('restarts');
}

if(typeof module!=='undefined'&&module.exports){
  module.exports={gen16Generate, gen16SolveMRV, gen16SolveBasic, gen16RandomRegions, gen16Neighbors4, gen16Rng, gen16Shuffle, gen16ConnectedWithout, gen16Popcount};
}
