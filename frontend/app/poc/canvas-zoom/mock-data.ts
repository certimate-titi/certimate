// POC: 192 mock nodes (6 領域 × 4 主題 × 8 節點)
export type CanvasNode = {
  id: string;
  name: string;
  tier: 1 | 2 | 3;
  parentId: string | null;
  mastery: number;
  questionCount: number;
  wrongAnswerCount: number;
};

const DOMAINS = ['AI 基礎', '機器學習', '深度學習', '大數據', '雲端', '資料科學'];
const TOPIC_TEMPLATES = ['基本概念', '演算法', '實作應用', '評估與優化'];
const NODE_TEMPLATES = ['定義', '原理', '公式', '範例', '應用', '限制', '優化', '延伸'];

export function generateMockNodes(): CanvasNode[] {
  const nodes: CanvasNode[] = [];

  DOMAINS.forEach((domain, di) => {
    const domainId = `d${di}`;
    nodes.push({
      id: domainId,
      name: domain,
      tier: 1,
      parentId: null,
      mastery: 0.3 + Math.random() * 0.6,
      questionCount: 30 + Math.floor(Math.random() * 50),
      wrongAnswerCount: Math.floor(Math.random() * 10),
    });

    TOPIC_TEMPLATES.forEach((topic, ti) => {
      const topicId = `${domainId}-t${ti}`;
      nodes.push({
        id: topicId,
        name: `${domain}-${topic}`,
        tier: 2,
        parentId: domainId,
        mastery: Math.random(),
        questionCount: 8 + Math.floor(Math.random() * 15),
        wrongAnswerCount: Math.floor(Math.random() * 5),
      });

      NODE_TEMPLATES.forEach((node, ni) => {
        nodes.push({
          id: `${topicId}-n${ni}`,
          name: `${node}${ni + 1}`,
          tier: 3,
          parentId: topicId,
          mastery: Math.random(),
          questionCount: 1 + Math.floor(Math.random() * 5),
          wrongAnswerCount: Math.floor(Math.random() * 3),
        });
      });
    });
  });

  return nodes;
}

export function masteryToStatus(m: number): 'red' | 'yellow' | 'green' | 'gray' {
  if (m < 0.3) return 'red';
  if (m < 0.6) return 'yellow';
  if (m < 0.85) return 'green';
  return 'green';
}

export function masteryToColor(m: number): string {
  if (m < 0.3) return '#ef4444';
  if (m < 0.6) return '#f59e0b';
  if (m < 0.85) return '#10b981';
  return '#059669';
}
