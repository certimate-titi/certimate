/**
 * Web Worker: 客戶端遞迴聚合 parent progress（動態知識庫核心）
 *
 * 不需要 DB I/O — 每個節點的 effective_progress 由 API 提供，
 * parent 的聚合進度在此 Worker 中遞迴計算。
 *
 * Input message:
 *   { type: 'AGGREGATE', nodes: FlatNode[] }
 *
 * FlatNode:
 *   { id, parentId, effectiveProgress, weight, depth, name }
 *
 * Output message:
 *   { type: 'RESULT', aggregated: { [nodeId]: { aggregatedProgress, childCount, decayStatus } } }
 */

self.onmessage = function (e) {
  if (e.data.type === 'AGGREGATE') {
    const result = aggregateProgress(e.data.nodes);
    self.postMessage({ type: 'RESULT', aggregated: result });
  }
};

function aggregateProgress(flatNodes) {
  // Build parent-children map
  const childrenMap = {}; // parentId -> [node, ...]
  const nodeMap = {};     // id -> node

  for (const node of flatNodes) {
    nodeMap[node.id] = { ...node, aggregatedProgress: node.effectiveProgress };
    if (node.parentId) {
      if (!childrenMap[node.parentId]) childrenMap[node.parentId] = [];
      childrenMap[node.parentId].push(node);
    }
  }

  // Find root nodes (no parent or parent not in set)
  const roots = flatNodes.filter(n => !n.parentId || !nodeMap[n.parentId]);

  // Bottom-up aggregation: process deepest nodes first
  const maxDepth = Math.max(...flatNodes.map(n => n.depth || 0), 0);

  for (let depth = maxDepth; depth >= 0; depth--) {
    for (const node of flatNodes) {
      if ((node.depth || 0) !== depth) continue;

      const children = childrenMap[node.id];
      if (children && children.length > 0) {
        // Weighted average of children's aggregated progress
        let totalWeight = 0;
        let weightedSum = 0;

        for (const child of children) {
          const childAgg = nodeMap[child.id];
          const w = child.weight || 1.0;
          weightedSum += (childAgg.aggregatedProgress || 0) * w;
          totalWeight += w;
        }

        nodeMap[node.id].aggregatedProgress = totalWeight > 0
          ? weightedSum / totalWeight
          : 0;
      }
    }
  }

  // Build result
  const result = {};
  for (const [id, node] of Object.entries(nodeMap)) {
    const children = childrenMap[id] || [];
    const progress = node.aggregatedProgress || 0;

    result[id] = {
      aggregatedProgress: Math.round(progress * 10000) / 10000,
      childCount: children.length,
      decayStatus: progress >= 0.7 ? 'fresh' :
                   progress >= 0.4 ? 'decaying' :
                   progress > 0 ? 'critical' : 'unseen',
    };
  }

  return result;
}
