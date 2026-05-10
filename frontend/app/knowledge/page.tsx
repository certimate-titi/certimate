/**
 * @file 路由 `/knowledge` — 知識地圖頁。
 *
 * 主學習介面：左側知識樹／圖譜，右側節點詳情面板（含學習鷹架）；
 * 透過 query string `subjectId` 與 `resourceId` 切換科目／聚焦特定資源；
 * 整合 `knowledgeService` / `documentService` / `resourceParseService`。
 */
'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { FileText, Youtube, Search, Network, Send, Lock, Trash2, AlertTriangle, MessageCircle, ExternalLink, BookOpen, RefreshCw, Image, ChevronDown, ChevronRight, ClipboardList, X, NotebookPen, Sparkles } from 'lucide-react';
import { knowledgeService, subjectService, documentService, resourceParseService } from '@/lib/api/services';
import OrphanCoachPanel from '@/components/coach/OrphanCoachPanel';
import HardDeleteConfirmModal, { type CascadeCount } from '@/components/HardDeleteConfirmModal';
import type { Document, KnowledgeNode, GetNodeDetailResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import { useIsEmbedded } from '@/lib/embed-context';
import { useIsMobile } from '@/hooks/use-mobile';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import MathContent from '@/components/MathContent';
import MindMapTree, { type MindMapNode } from '@/components/MindMapTree';
import ForceGraph, { type GraphNode } from '@/components/ForceGraph';
import NodeDetailPanel, { type NodeDetailTab } from '@/components/NodeDetailPanel';
import ScaffoldMaterial from '@/components/ScaffoldMaterial';
import ScaffoldNotebook from '@/components/ScaffoldNotebook';
import ScaffoldReplayCard from '@/components/ScaffoldReplayCard';
// react-resizable-panels removed — using plain flex layout

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

function KnowledgeBasePageInner() {
  const embedded = useIsEmbedded();
  const { isAuthenticated, loading: authLoading, onboardingCompleted, isProPlus, subscriptionTier } = useAuth();
  const isPro199 = subscriptionTier === 'PRO_199';
  const router = useRouter();
  const searchParams = useSearchParams();
  const focusResourceId = searchParams.get('resourceId');
  const focusSubjectId = searchParams.get('subjectId');
  const initialTab = searchParams.get('tab');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedNodeDetail, setSelectedNodeDetail] = useState<GetNodeDetailResponse | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [nodes, setNodes] = useState<KnowledgeNode[]>([]);
  const [mindMapNodes, setMindMapNodes] = useState<MindMapNode[]>([]);
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [freeQueriesLeft, setFreeQueriesLeft] = useState(() => {
    if (isPro199) return 0;
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('certimate_ai_coach_free_queries');
      if (saved !== null) return Math.max(0, parseInt(saved, 10));
    }
    return 3;
  });
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);
  const [docChunks, setDocChunks] = useState<Record<string, Array<{ id: string; chunk_index: number; content: string; section_title: string; depth: number; chunk_type: string; source_page_start: number | null; source_page_end: number | null }>>>({});
  const [loadingChunks, setLoadingChunks] = useState<string | null>(null);
  const [chunkErrors, setChunkErrors] = useState<Record<string, string>>({});
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [deletePreviewCascade, setDeletePreviewCascade] = useState<CascadeCount>({});
  const [deletePreviewLoading, setDeletePreviewLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteConfirmLoading, setDeleteConfirmLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState<string | null>(null);
  const [graphView, setGraphView] = useState<'tree' | 'force'>('force');
  const [centerView, setCenterView] = useState<'graph' | 'document'>('graph');
  const [parseJobFailures, setParseJobFailures] = useState<Record<string, string>>({});
  const [docFullText, setDocFullText] = useState<string>('');
  const [docFullTitle, setDocFullTitle] = useState<string>('');
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const isMobile = useIsMobile();
  const [mobileDrawer, setMobileDrawer] = useState<'left' | 'right' | null>(null);
  const [activeNodeTab, setActiveNodeTab] = useState<NodeDetailTab>(() => {
    // 鷹架已整合回 info tab，tab=material graceful fallback 為 info
    const valid: NodeDetailTab[] = ['info', 'notebook', 'coach'];
    return (valid.includes(initialTab as NodeDetailTab) ? initialTab : 'info') as NodeDetailTab;
  });
  // Orphan AI 教練：切換蘇格拉底對話面板
  const [showOrphanCoach, setShowOrphanCoach] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // On mobile, collapse both panels by default
  useEffect(() => {
    if (isMobile) {
      setShowLeftPanel(false);
      setShowRightPanel(false);
    } else {
      setShowLeftPanel(true);
      setShowRightPanel(true);
    }
    setMobileDrawer(null);
  }, [isMobile]);

  // V3: 轉換 MindMapNode[] → GraphNode[] for ForceGraph
  const graphNodes: GraphNode[] = (() => {
    const flat: GraphNode[] = [];
    const flatten = (nodes: MindMapNode[]) => {
      for (const n of nodes) {
        flat.push({
          id: n.id,
          name: n.name,
          depth: n.depth,
          progress: n.mastery_rate || 0,
          color: n.mastery_color || 'gray',
          parentId: n.parent_id,
          status: n.status || 'UNSEEN',
          availableQuestions: 0,
        });
        if (n.children) flatten(n.children);
      }
    };
    flatten(mindMapNodes);
    return flat;
  })();

  // Load subjects + guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.replace('/login'); return; }
    if (!onboardingCompleted) { router.replace('/onboarding'); return; }

    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (res.subjects.length > 0) {
        // Priority: query param subjectId > localStorage > first subject
        // Match either UserSubject.id or underlying subjectId (resource.subject_id 為後者)
        const queryMatch = focusSubjectId && res.subjects.find(
          (s: UserSubject) => s.id === focusSubjectId || s.subjectId === focusSubjectId
        );
        if (queryMatch) {
          setActiveSubjectId(queryMatch.id);
          localStorage.setItem('certimate_active_subject_id', queryMatch.id);
          return;
        }
        const saved = localStorage.getItem('certimate_active_subject_id');
        const match = saved && res.subjects.find((s: UserSubject) => s.id === saved);
        setActiveSubjectId(match ? saved : res.subjects[0].id);
      }
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load knowledge map by active subject
  useEffect(() => {
    if (!activeSubjectId) return;
    setLoadingDocs(true);
    setLoadingDetail(false);
    setSelectedNodeDetail(null);
    setChatMessages([]);
    // 不重置 freeQueriesLeft — 切換科目不應消耗免費次數
    setDeleteConfirmId(null);
    setCenterView('graph');
    setDocFullText('');
    setDocFullTitle('');
    setExpandedDocId(null);

    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    knowledgeService.getMap(targetSubjectId).then((mapRes: Record<string, unknown>) => {
      const rawResources = (mapRes.resources || mapRes.documents || []) as Array<Record<string, string>>;
      const allDocuments: Document[] = rawResources.map(r => {
        // Map backend status → frontend Document status
        // Backend ResourceStatus enum: pending / processing / completed / failed / completed_no_map
        const backendStatus = (r.status || 'pending').toString().toLowerCase();
        let feStatus: Document['status'] = 'PROCESSING';
        if (backendStatus === 'completed' || backendStatus === 'completed_no_map') feStatus = 'COMPLETED';
        else if (backendStatus === 'failed') feStatus = 'FAILED';
        else if (backendStatus === 'pending' || backendStatus === 'processing') feStatus = 'PROCESSING';
        return {
          id: r.id,
          userId: '',
          title: r.name || r.title || '',
          sourceType: (r.type || r.resource_type || 'pdf') as Document['sourceType'],
          subjectId: targetSubjectId,
          sourceUrl: r.source_url || '',
          mcpParsedTranscriptUrl: null,
          status: feStatus,
          fileSizeBytes: 0,
          visionRequired: false,
          createdAt: r.created_at || new Date().toISOString(),
        };
      });
      const allNodes = ((mapRes.nodes || []) as KnowledgeNode[]);
      setDocuments(allDocuments);
      setNodes(allNodes);
      setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
      const focused = focusResourceId && allDocuments.some(d => d.id === focusResourceId)
        ? focusResourceId
        : (allDocuments[0]?.id ?? null);
      setSelectedDocId(focused);
      if (focused && focusResourceId === focused) {
        setExpandedDocId(focused);
      }
      setLoadingDocs(false);
    }).catch(() => setLoadingDocs(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSubjectId]);

  // Polling: refresh resource statuses every 5s while any are PROCESSING.
  // Stops automatically once all resources are COMPLETED or FAILED.
  useEffect(() => {
    const hasPending = documents.some(d => d.status === 'PROCESSING');
    if (!hasPending || !activeSubjectId) return;
    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;
    const timer = setInterval(() => {
      knowledgeService.getMap(targetSubjectId).then((mapRes: Record<string, unknown>) => {
        const rawResources = (mapRes.resources || mapRes.documents || []) as Array<Record<string, string>>;
        setDocuments(prev => {
          const updated = rawResources.map(r => {
            const backendStatus = (r.status || 'pending').toString().toLowerCase();
            let feStatus: Document['status'] = 'PROCESSING';
            if (backendStatus === 'completed' || backendStatus === 'completed_no_map') feStatus = 'COMPLETED';
            else if (backendStatus === 'failed') feStatus = 'FAILED';
            const existing = prev.find(d => d.id === r.id);
            return existing ? { ...existing, status: feStatus } : existing;
          }).filter(Boolean) as Document[];
          // Keep order from previous list, append new ones
          const existingIds = new Set(updated.map(d => d.id));
          return [...updated, ...prev.filter(d => !existingIds.has(d.id))];
        });
        // If extraction just finished, also refresh nodes
        const justCompleted = rawResources.some(r => {
          const bs = (r.status || '').toString().toLowerCase();
          const prev = documents.find(d => d.id === r.id);
          return (bs === 'completed' || bs === 'completed_no_map') && prev?.status === 'PROCESSING';
        });
        if (justCompleted) {
          const newNodes = (mapRes.nodes || []) as KnowledgeNode[];
          setNodes(newNodes);
          setMindMapNodes(newNodes as unknown as MindMapNode[]);
        }
      }).catch(() => { /* silent — next tick retries */ });
    }, 5000);
    return () => clearInterval(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents.map(d => `${d.id}:${d.status}`).join(','), activeSubjectId]);

  // Layer 3 空態查 Job 表: 當有 FAILED 的文件，自動查詢 failure_reason
  useEffect(() => {
    const failedDocs = documents.filter(d => d.status === 'FAILED');
    if (failedDocs.length === 0) return;
    failedDocs.forEach(doc => {
      if (parseJobFailures[doc.id]) return; // 已查過
      resourceParseService.getStatus(doc.id).then(res => {
        if (res.failure_reason) {
          setParseJobFailures(prev => ({ ...prev, [doc.id]: res.failure_reason! }));
        }
      }).catch(() => { /* silent */ });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents.map(d => `${d.id}:${d.status}`).join(',')]);

  const handleNodeClick = async (nodeId: string) => {
    setLoadingDetail(true);
    setChatMessages([]);
    setFreeQueriesLeft(isPro199 ? 0 : 3);
    setShowOrphanCoach(false);
    try {
      const raw = await knowledgeService.getNodeDetail(nodeId) as unknown as Record<string, unknown>;
      const srcCitation = (raw.source_citation || {}) as Record<string, unknown>;
      const detail = {
        node: {
          id: nodeId,
          label: (raw.node_name as string) || '',
          name: (raw.node_name as string) || '',
          masteryLevel: 'not_tested' as string,
          masteryRate: 0,
        },
        citationSource: {
          type: (raw.source_type as string) || 'pdf',
          documentTitle: (raw.node_name as string) || '',
          page: (srcCitation.source_page_number as number) || null,
          timestampStart: (srcCitation.source_timestamp_seconds as number) || null,
          sourceUrl: '',
        },
        citationText: (raw.source_text as string) || '（無原文摘要）',
        sourceText: (raw.source_text as string) || '（無原文摘要）',
        sourceType: (raw.source_type as string) || 'pdf',
        sourceRef: (raw.source_ref as string) || '',
      } as unknown as GetNodeDetailResponse;
      setSelectedNodeDetail(detail);
    } catch { /* silent */ }
    setLoadingDetail(false);
  };

  // Auto-select node — prefer the focused resource's node so the right panel
  // (含教材/學習鷹架) reflects the resource the user clicked from /resource-library.
  // Spec 11 §「解析內容」入口應導向知識地圖並對焦該資源
  useEffect(() => {
    if (nodes.length > 0 && !selectedNodeDetail) {
      // Find a node belonging to the focused resource (recursive)
      const findResourceNode = (list: KnowledgeNode[]): KnowledgeNode | null => {
        for (const n of list) {
          const nAny = n as unknown as Record<string, unknown>;
          if (focusResourceId && (nAny.documentId === focusResourceId || nAny.resource_id === focusResourceId)) {
            return n;
          }
          if (n.children?.length) {
            const found = findResourceNode(n.children);
            if (found) return found;
          }
        }
        return null;
      };
      const focused = focusResourceId ? findResourceNode(nodes) : null;
      const target = focused
        ? (focused.children?.[0]?.id || focused.id)
        : (nodes[0].children?.[0]?.id || nodes[0].id);
      handleNodeClick(target);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSendChat = async (msg?: string) => {
    const text = msg || chatInput.trim();
    if (!text || chatLoading) return;
    if (isPro199) return;
    if (!isProPlus && freeQueriesLeft <= 0) return;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: text }]);
    setChatLoading(true);
    if (!isProPlus) setFreeQueriesLeft(q => {
      const next = q - 1;
      localStorage.setItem('certimate_ai_coach_free_queries', String(next));
      return next;
    });
    try {
      const { apiClient } = await import('@/lib/api/client');
      const res = await apiClient.post<{ message: string }>(`/knowledge-map/nodes/${selectedNodeDetail?.node.id}/chat`, { message: text });
      setChatMessages(prev => [...prev, { role: 'ai', content: res.message }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'ai', content: '抱歉，暫時無法回覆。請稍後再試。' }]);
    }
    setChatLoading(false);
  };

  const [deleteError, setDeleteError] = useState<string | null>(null);
  const removeDocLocally = (docId: string) => {
    setDocuments(prev => prev.filter(d => d.id !== docId));
    setNodes(prev => prev.filter(n => n.documentId !== docId));
    setDeleteConfirmId(null);
    if (selectedDocId === docId) setSelectedDocId(null);
  };
  const handleDeleteDocument = async (docId: string) => {
    setDeleteError(null);
    try {
      await documentService.delete(docId);
      removeDocLocally(docId);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '刪除失敗，請稍後再試';
      // 後端回 404「資源不存在」表示已不在 DB → 同步前端列表即可
      if (/不存在|not found|404/i.test(msg)) {
        removeDocLocally(docId);
        return;
      }
      setDeleteError(msg);
    }
  };

  // 開啟硬刪除 Modal（先取得 preview）
  const handleOpenDeleteModal = async (docId: string) => {
    setDeleteConfirmId(docId);
    setDeletePreviewCascade({});
    setDeletePreviewLoading(true);
    setDeleteModalOpen(true);
    try {
      const res = await documentService.getDeletePreview(docId);
      setDeletePreviewCascade(res.cascade_count ?? {});
    } catch {
      // preview 失敗仍允許繼續，cascade 顯示空
    } finally {
      setDeletePreviewLoading(false);
    }
  };

  // Modal 確認後執行真正刪除
  const handleConfirmHardDelete = async () => {
    if (!deleteConfirmId) return;
    setDeleteConfirmLoading(true);
    try {
      await documentService.delete(deleteConfirmId);
      removeDocLocally(deleteConfirmId);
      setDeleteModalOpen(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '刪除失敗，請稍後再試';
      if (/不存在|not found|404/i.test(msg)) {
        removeDocLocally(deleteConfirmId);
        setDeleteModalOpen(false);
        return;
      }
      setDeleteError(msg);
      setDeleteModalOpen(false);
    } finally {
      setDeleteConfirmLoading(false);
    }
  };

  const handleToggleDocChunks = async (docId: string) => {
    if (expandedDocId === docId) {
      setExpandedDocId(null);
      return;
    }
    setExpandedDocId(docId);
    const doc = documents.find(d => d.id === docId);
    // 虛擬考古題資源（hist: 前綴）走另一條 markdown 取得路徑，不打 chunks API
    if (docId.startsWith('hist:') || doc?.sourceType === 'historical_exam') {
      const hid = docId.startsWith('hist:') ? docId.slice(5) : docId;
      try {
        const md = await documentService.getHistoricalMarkdown(hid);
        setDocFullText(md.content || '（無題目內容）');
      } catch {
        setDocFullText('❌ 載入考古題內容失敗');
      }
      setDocFullTitle(doc?.title || '');
      setCenterView('document');
      return;
    }
    if (docChunks[docId]) {
      // Already cached — build full text and show
      const sorted = [...docChunks[docId]].sort((a, b) => a.chunk_index - b.chunk_index);
      setDocFullText(sorted.map(c => c.content).join('\n\n'));
      setDocFullTitle(doc?.title || '');
      setCenterView('document');
      return;
    }
    setLoadingChunks(docId);
    try {
      const res = await knowledgeService.getResourceChunks(docId) as { chunks: Array<{ id: string; chunk_index: number; content: string; section_title: string; depth: number; chunk_type: string; source_page_start: number | null; source_page_end: number | null }> };
      const chunks = res.chunks || [];
      setDocChunks(prev => ({ ...prev, [docId]: chunks }));
      setChunkErrors(prev => { const next = { ...prev }; delete next[docId]; return next; });
      // Build full text and switch to document view
      const sorted = [...chunks].sort((a, b) => a.chunk_index - b.chunk_index);
      setDocFullText(sorted.map(c => c.content).join('\n\n'));
      setDocFullTitle(doc?.title || '');
      setCenterView('document');
    } catch (err) {
      const errMsg = (err as Error)?.message || '';
      const msg = errMsg.includes('無權') ? '無權存取此資源'
        : errMsg.includes('不存在') ? '資源不存在'
        : '載入失敗，請稍後再試';
      setChunkErrors(prev => ({ ...prev, [docId]: msg }));
    }
    setLoadingChunks(null);
  };

  const sourceTypeIcons: Record<string, { icon: typeof FileText; color: string }> = {
    PDF: { icon: FileText, color: 'text-blue-500' },
    MARKDOWN: { icon: FileText, color: 'text-slate-500' },
    YOUTUBE_URL: { icon: Youtube, color: 'text-red-500' },
    IMAGE_MATH: { icon: FileText, color: 'text-purple-500' },
    HISTORICAL_EXAM: { icon: ClipboardList, color: 'text-emerald-600' },
    historical_exam: { icon: ClipboardList, color: 'text-emerald-600' },
  };

  // 根據節點上下文與最近對話動態生成 quickChips（前文感知）
  const quickChips = (() => {
    const node = selectedNodeDetail?.node as { label?: string; name?: string; mastery_rate?: number } | undefined;
    const nodeName = node?.name || node?.label || '此概念';
    const mastery = node?.mastery_rate ?? 0;
    const lastUserMsg = [...chatMessages].reverse().find(m => m.role === 'user')?.content || '';
    const lastAiMsg = [...chatMessages].reverse().find(m => m.role === 'ai')?.content || '';

    // 第一次提問 — 基礎切入
    if (chatMessages.length === 0) {
      if (mastery < 40) {
        return [`「${nodeName}」是什麼？`, '用最簡單的話解釋', '常見迷思有哪些？'];
      }
      if (mastery >= 70) {
        return [`「${nodeName}」進階觀點`, '常考考點與陷阱', '相關延伸知識'];
      }
      return [`解釋「${nodeName}」`, '給我一個例子', '幫我出 1 題練習'];
    }

    // 已有對話 — 依最後 AI 回覆延伸
    if (lastAiMsg.length > 0) {
      // 例子已給 → 引導應用
      if (/例如|例子|舉例/.test(lastAiMsg) || /例|範例/.test(lastUserMsg)) {
        return ['再深入一點', '出 1 題小測驗驗證', '與其他概念有何不同？'];
      }
      // 解釋給了 → 引導實作
      if (/定義|是指|意思是/.test(lastAiMsg)) {
        return ['給我一個例子', '常見錯誤是什麼？', '考試常考方向'];
      }
      // 出題後 → 引導反思
      if (/題目|選項|請選擇/.test(lastAiMsg)) {
        return ['解析答案', '為什麼其他選項不對？', '相關考點'];
      }
    }

    // fallback — 通用 chip
    return ['再深入一點', '給我一個例子', '常見錯誤是什麼？'];
  })();

  const showSubjectSwitcher = subjects.length > 0;
  const containerHeightClass = 'h-[calc(100dvh-64px)]';

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      <div className={`flex-1 flex flex-col ${containerHeightClass} overflow-hidden bg-slate-50`}>
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-3 md:px-6 py-2 md:py-3 flex items-center justify-between shrink-0 gap-2">
          {!embedded && (
            <div className="min-w-0">
              <h1 className="text-base md:text-xl font-bold text-slate-900 truncate">知識庫</h1>
              <p className="text-[10px] md:text-xs text-slate-500 hidden sm:block">左側選擇資源，中間瀏覽內容，右側探索心智圖與 AI 教練</p>
            </div>
          )}
          <div className="flex items-center gap-2 md:gap-3 shrink-0">
            {showSubjectSwitcher && (
              <SubjectSwitcher
                subjects={subjects}
                activeSubjectId={activeSubjectId}
                onSwitch={(id) => { setActiveSubjectId(id); localStorage.setItem('certimate_active_subject_id', id); }}
                onAddSubject={() => router.push('/onboarding')}
                allowAdd={false}
                variant="compact"
              />
            )}
            {/* Mobile drawer toggles */}
            {isMobile && (
              <>
                <button
                  onClick={() => setMobileDrawer(mobileDrawer === 'left' ? null : 'left')}
                  className={`p-1.5 rounded-lg transition-colors ${mobileDrawer === 'left' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}
                  title="資料列表"
                >
                  <BookOpen className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setMobileDrawer(mobileDrawer === 'right' ? null : 'right')}
                  className={`p-1.5 rounded-lg transition-colors ${mobileDrawer === 'right' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}
                  title="說明 & AI 教練"
                >
                  <MessageCircle className="h-4 w-4" />
                </button>
              </>
            )}
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜尋知識點..."
                className="pl-9 pr-4 py-1.5 rounded-full border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-36 lg:w-48"
              />
            </div>
            <Link href={`/knowledge/wrong-answers${activeSubjectId ? `?subjectId=${activeSubjectId}` : ''}`} className="bg-rose-500 text-white px-2 md:px-3 py-1 md:py-1.5 rounded-full text-xs md:text-sm font-medium hover:bg-rose-600 transition-colors whitespace-nowrap" data-testid="open-wrong-answer-heatmap" title="錯題地圖">
              🔥<span className="hidden md:inline ml-1">錯題地圖</span>
            </Link>
            <Link href="/dashboard" className="bg-emerald-500 text-white px-2 md:px-3 py-1 md:py-1.5 rounded-full text-xs md:text-sm font-medium hover:bg-emerald-600 transition-colors whitespace-nowrap" title="新增資源">
              +<span className="hidden md:inline ml-1">新增資源</span>
            </Link>
          </div>
        </header>

        {/* ===== THREE-COLUMN RESIZABLE LAYOUT ===== */}
        <div className="flex-1 flex overflow-hidden relative">

          {/* Mobile overlay backdrop */}
          {isMobile && mobileDrawer && (
            <div
              className="absolute inset-0 bg-black/30 z-20"
              onClick={() => setMobileDrawer(null)}
            />
          )}

          {/* ── LEFT: Resource List ── */}
          {(showLeftPanel || (isMobile && mobileDrawer === 'left')) && (
            <div className={`${isMobile ? 'absolute left-0 top-0 bottom-0 z-30 w-[85vw] max-w-[320px] shadow-xl' : 'w-[240px] lg:w-[280px]'} shrink-0 border-r border-slate-200`}>
              <div className="h-full flex flex-col bg-white">
                <div className="p-3 border-b border-slate-100 flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-emerald-500" />
                  <h2 className="text-sm font-semibold text-slate-700">資料列表</h2>
                  <span className="ml-auto text-[10px] text-slate-400">{documents.length} 筆</span>
                  {isMobile && (
                    <button onClick={() => setMobileDrawer(null)} className="p-1 rounded hover:bg-slate-100">
                      <X className="h-4 w-4 text-slate-400" />
                    </button>
                  )}
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {loadingDocs ? (
                    [1, 2, 3].map(i => <div key={i} className="bg-slate-100 rounded-lg animate-pulse h-12" />)
                  ) : documents.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 text-xs">
                      <BookOpen className="h-5 w-5 mx-auto mb-1 text-slate-300" />
                      尚無資源，請上傳學習教材
                    </div>
                  ) : (
                    documents.filter(d => !searchQuery || d.title.toLowerCase().includes(searchQuery.toLowerCase())).map(doc => {
                      const isActive = doc.id === selectedDocId;
                      const isExpanded = doc.id === expandedDocId;
                      const { icon: Icon, color } = sourceTypeIcons[doc.sourceType] || sourceTypeIcons.PDF;
                      const chunks = docChunks[doc.id];
                      return (
                        <div key={doc.id} className={`rounded-lg border transition-colors ${isActive ? 'border-emerald-200 bg-emerald-50/50' : 'border-transparent hover:border-slate-200'}`}>
                          <div
                            onClick={() => { setSelectedDocId(doc.id); handleToggleDocChunks(doc.id); const docNode = nodes.find(n => n.documentId === doc.id); if (docNode) handleNodeClick(docNode.children?.[0]?.id || docNode.id); }}
                            className="group p-2.5 cursor-pointer"
                          >
                            <div className="flex items-center gap-2">
                              <Icon className={`h-4 w-4 shrink-0 ${color}`} />
                              <div className="flex-1 min-w-0">
                                <h3 className="text-xs font-medium truncate">{doc.title}</h3>
                                <p className="text-[10px] text-slate-400 flex items-center gap-1">
                                  {doc.sourceType}
                                  {doc.status === 'PROCESSING' && (
                                    <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 text-[9px] font-medium">
                                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                                      處理中
                                    </span>
                                  )}
                                  {doc.status === 'FAILED' && (
                                    <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[9px] font-medium" title={parseJobFailures[doc.id] || ''}>
                                      <AlertTriangle className="w-2.5 h-2.5" />
                                      {parseJobFailures[doc.id] ? `失敗：${parseJobFailures[doc.id].slice(0, 30)}${parseJobFailures[doc.id].length > 30 ? '...' : ''}` : '失敗'}
                                    </span>
                                  )}
                                  {doc.status === 'COMPLETED' && (
                                    <span className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-[9px] font-medium">
                                      ✓ 完成
                                    </span>
                                  )}
                                </p>
                              </div>
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  setSelectedDocId(doc.id);
                                  // Status-aware fallback messages
                                  const statusMsg = doc.status === 'PROCESSING'
                                    ? '⏳ 此資源仍在處理中（PDF 解析 → 文字切塊 → 向量化）。系統每 5 秒自動更新狀態，請稍後再試。'
                                    : doc.status === 'FAILED'
                                      ? (doc.errorMessage
                                          ? `❌ 處理失敗：${doc.errorMessage}\n\n請刪除後修正問題並重新上傳。`
                                          : '❌ 此資源處理失敗，請刪除後重新上傳，或聯繫管理員。')
                                      : '（尚無可顯示內容）';

                                  // Historical exam virtual resource — render markdown from backend
                                  if (doc.sourceType === 'historical_exam' || doc.id.startsWith('hist:')) {
                                    const hid = doc.id.startsWith('hist:') ? doc.id.slice(5) : doc.id;
                                    try {
                                      const md = await documentService.getHistoricalMarkdown(hid);
                                      setDocFullText(md.content || '（無題目內容）');
                                    } catch {
                                      setDocFullText('❌ 載入考古題內容失敗');
                                    }
                                    setDocFullTitle(doc.title);
                                    setCenterView('document');
                                    return;
                                  }
                                  // Fetch chunks if not cached
                                  let fullText = '';
                                  if (!docChunks[doc.id]) {
                                    setLoadingChunks(doc.id);
                                    try {
                                      const res = await knowledgeService.getResourceChunks(doc.id) as { chunks: Array<{ id: string; chunk_index: number; content: string; section_title: string; depth: number; chunk_type: string; source_page_start: number | null; source_page_end: number | null }> };
                                      const chunks = res.chunks || [];
                                      setDocChunks(prev => ({ ...prev, [doc.id]: chunks }));
                                      const sorted = [...chunks].sort((a, b) => a.chunk_index - b.chunk_index);
                                      fullText = sorted.map(c => c.content).join('\n\n');
                                    } catch {
                                      fullText = '';
                                    } finally {
                                      setLoadingChunks(null);
                                    }
                                  } else {
                                    const sorted = [...docChunks[doc.id]].sort((a, b) => a.chunk_index - b.chunk_index);
                                    fullText = sorted.map(c => c.content).join('\n\n');
                                  }

                                  // Fallback: system-generated resources (e.g. 考古題題庫) have no
                                  // chunks but the backend exposes a rolled-up summary via
                                  // /knowledge-map/resources/{id}/summary that walks the
                                  // synthetic knowledge_nodes subtree and returns a readable doc.
                                  if (!fullText || fullText.length < 20) {
                                    try {
                                      const summary = await knowledgeService.getResourceSummary(doc.id);
                                      if (summary?.content && summary.content.length > 20) {
                                        fullText = summary.content;
                                      }
                                    } catch { /* silent */ }
                                  }

                                  setDocFullText(fullText || statusMsg);
                                  setDocFullTitle(doc.title);
                                  setCenterView('document');
                                }}
                                className="text-[10px] font-medium text-blue-600 hover:text-blue-700 px-1.5 py-0.5 rounded hover:bg-blue-50 shrink-0 whitespace-nowrap"
                                title="查看原文"
                              >
                                📖 原文
                              </button>
                              {!doc.id.startsWith('hist:') && (
                                <button onClick={(e) => { e.stopPropagation(); void handleOpenDeleteModal(doc.id); }} className="text-slate-400 hover:text-rose-500 transition-colors shrink-0 p-1" title="刪除資源"><Trash2 className="h-3.5 w-3.5" /></button>
                              )}
                            </div>
                          </div>
                          {isExpanded && (
                            <div className="px-2 pb-2">
                              {loadingChunks === doc.id ? (
                                <div className="flex items-center justify-center py-3">
                                  <div className="w-3 h-3 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                                </div>
                              ) : chunks && chunks.length > 0 ? (
                                <div className="space-y-0.5 max-h-[280px] overflow-y-auto">
                                  {chunks.map(chunk => (
                                    <div
                                      key={chunk.id}
                                      className={`px-2 py-1.5 rounded text-[10px] leading-relaxed ${
                                        chunk.chunk_type === 'exam_questions'
                                          ? 'bg-amber-50 border border-amber-100'
                                          : chunk.chunk_type === 'image_analysis'
                                            ? 'bg-purple-50 border border-purple-100'
                                            : 'bg-slate-50 hover:bg-slate-100'
                                      }`}
                                    >
                                      <div className="flex items-start gap-1.5">
                                        {chunk.chunk_type === 'exam_questions' ? (
                                          <ClipboardList className="h-3 w-3 shrink-0 text-amber-600 mt-0.5" />
                                        ) : chunk.chunk_type === 'image_analysis' ? (
                                          <Image className="h-3 w-3 shrink-0 text-purple-500 mt-0.5" />
                                        ) : (
                                          <FileText className="h-3 w-3 shrink-0 text-slate-400 mt-0.5" />
                                        )}
                                        <div className="flex-1 min-w-0">
                                          {chunk.chunk_type === 'exam_questions' && (
                                            <span className="inline-block px-1 py-0 rounded text-[8px] font-semibold text-amber-700 bg-amber-100 mb-0.5">考古題</span>
                                          )}
                                          {chunk.chunk_type === 'image_analysis' && (
                                            <span className="inline-block px-1 py-0 rounded text-[8px] font-semibold text-purple-600 bg-purple-100 mb-0.5">圖片分析</span>
                                          )}
                                          <p className="font-medium text-slate-700 truncate">
                                            {chunk.section_title || `段落 ${chunk.chunk_index + 1}`}
                                          </p>
                                          <p className="text-slate-500 line-clamp-2 mt-0.5">{chunk.content.slice(0, 120)}{chunk.content.length > 120 ? '...' : ''}</p>
                                          {chunk.chunk_type !== 'exam_questions' && chunk.source_page_start && (
                                            <span className="text-[9px] text-slate-400 mt-0.5 inline-block">p.{chunk.source_page_start}{chunk.source_page_end && chunk.source_page_end !== chunk.source_page_start ? `-${chunk.source_page_end}` : ''}</span>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : chunkErrors[doc.id] ? (
                                <div className="text-center py-2 text-[10px] text-rose-500">{chunkErrors[doc.id]}</div>
                              ) : (
                                <div className="text-center py-2 text-[10px] text-slate-400">尚無內容分塊</div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── CENTER: 知識圖譜 ── */}
          <div className="flex-1 min-w-0">
            <div className="h-full flex flex-col overflow-hidden bg-white">
              {/* Toolbar */}
              <div className="flex items-center justify-between px-2 md:px-3 py-1.5 border-b border-slate-100 bg-slate-50/50 shrink-0 gap-1 overflow-x-auto">
                <div className="flex items-center gap-1 md:gap-2 shrink-0">
                  {!isMobile && (
                    <button onClick={() => setShowLeftPanel(!showLeftPanel)} className={`px-2 py-1 text-[10px] rounded font-medium transition-colors whitespace-nowrap ${showLeftPanel ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                      {showLeftPanel ? '◀ 隱藏資料' : '▶ 資料列表'}
                    </button>
                  )}
                  <div className="flex bg-slate-100 rounded-md p-0.5">
                    <button onClick={() => { setGraphView('force'); setCenterView('graph'); }} className={`px-1.5 md:px-2 py-0.5 text-[10px] rounded font-medium whitespace-nowrap ${centerView === 'graph' && graphView === 'force' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-400'}`}>🌐 圖譜</button>
                    <button onClick={() => { setGraphView('tree'); setCenterView('graph'); }} className={`px-1.5 md:px-2 py-0.5 text-[10px] rounded font-medium whitespace-nowrap ${centerView === 'graph' && graphView === 'tree' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-400'}`}>📋 列表</button>
                    {docFullText && <button onClick={() => setCenterView('document')} className={`px-1.5 md:px-2 py-0.5 text-[10px] rounded font-medium whitespace-nowrap ${centerView === 'document' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-400'}`}>📄 文件</button>}
                  </div>
                  <div className="hidden md:flex items-center gap-2 text-[9px] text-slate-400 ml-2">
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />精熟</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-500" />部分</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" />弱</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-slate-300" />未測</span>
                  </div>
                  <button
                    onClick={async () => {
                      if (extracting || !activeSubjectId) return;
                      const activeSubject = subjects.find(s => s.id === activeSubjectId);
                      const targetSubjectId = activeSubject?.subjectId || activeSubjectId;
                      setExtracting(true);
                      setExtractResult(null);
                      try {
                        const res = await knowledgeService.extractKnowledgeTree(targetSubjectId);
                        const created = (res as Record<string, number>).nodes_created || 0;
                        setExtractResult(`✅ 萃取完成：${created} 個知識節點`);
                        // 重新載入知識圖譜
                        const mapRes = await knowledgeService.getMap(targetSubjectId) as Record<string, unknown>;
                        setNodes((mapRes.nodes || []) as KnowledgeNode[]);
                        setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
                      } catch (err) {
                        const msg = err instanceof Error ? err.message : String(err);
                        setExtractResult(`❌ 萃取失敗：${msg}`);
                      } finally {
                        setExtracting(false);
                        setTimeout(() => setExtractResult(null), 8000);
                      }
                    }}
                    disabled={extracting || !activeSubjectId}
                    className={`flex items-center gap-1 px-1.5 md:px-2 py-0.5 text-[10px] rounded font-medium ml-1 md:ml-2 transition-colors whitespace-nowrap ${
                      extracting
                        ? 'bg-blue-100 text-blue-500 cursor-wait'
                        : 'bg-slate-100 text-slate-500 hover:bg-blue-50 hover:text-blue-600'
                    }`}
                    title="重新分析：合併考古題與上傳教材，AI 統一萃取知識樹"
                  >
                    <RefreshCw className={`w-3 h-3 ${extracting ? 'animate-spin' : ''}`} />
                    {extracting ? '分析中...' : '重新分析'}
                  </button>
                  {extractResult && (
                    <span className="text-[10px] ml-1 text-blue-600">{extractResult}</span>
                  )}
                </div>
                {!isMobile && (
                  <button onClick={() => setShowRightPanel(!showRightPanel)} className={`px-2 py-1 text-[10px] rounded font-medium transition-colors whitespace-nowrap ${showRightPanel ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                    {showRightPanel ? '說明 & AI ▶' : '◀ 說明 & AI'}
                  </button>
                )}
              </div>
              {/* Graph / Document */}
              <div className="flex-1 overflow-hidden">
                {centerView === 'document' ? (
                  <div className="h-full overflow-y-auto px-4 md:px-8 py-4">
                    <h2 className="text-lg font-bold text-slate-800 mb-4">{docFullTitle}</h2>
                    <div className="prose prose-sm prose-slate max-w-none whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                      {docFullText}
                    </div>
                  </div>
                ) : !loadingDocs && mindMapNodes.length === 0 ? (
                  /* Layer 3 空態區分 + Spec 03b §空地圖 polish：4 種情境各自精準 CTA */
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center py-12 px-6 max-w-md">
                      {documents.length === 0 ? (
                        // 情境 1：從未上傳資源
                        <>
                          <div className="text-6xl mb-3">📚</div>
                          <p className="text-lg text-slate-700 font-bold mb-2">開始你的學習旅程</p>
                          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
                            上傳第一份學習資源，AI 自動建構知識心智圖、生成題目、追蹤掌握度。
                          </p>
                          <Link
                            href="/dashboard?openUpload=1"
                            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-full font-bold text-sm hover:bg-emerald-600 transition-colors shadow-md shadow-emerald-200"
                          >
                            📤 上傳第一份資源
                          </Link>
                          <div className="mt-4 text-xs text-slate-400">或直接從考古題題庫開始 →</div>
                        </>
                      ) : documents.every(d => d.status === 'FAILED') ? (
                        // 情境 2：全部解析失敗
                        <>
                          <AlertTriangle className="h-12 w-12 text-rose-400 mx-auto mb-3" />
                          <p className="text-lg text-rose-600 font-bold mb-2">所有資源解析失敗</p>
                          <p className="text-xs text-slate-500 mb-4 leading-relaxed">
                            {Object.values(parseJobFailures).length > 0
                              ? `常見原因：${Object.values(parseJobFailures)[0].slice(0, 60)}`
                              : '請檢查資源格式或聯繫管理員'}
                          </p>
                          <button
                            onClick={async () => {
                              if (!confirm(`一鍵重新解析所有 ${documents.length} 筆失敗資源？`)) return;
                              try {
                                const { resourceLibraryService } = await import('@/lib/api/services');
                                const res = await resourceLibraryService.batchReparseFailed(activeSubjectId);
                                alert(`已重新觸發 ${res.count} 筆資源解析`);
                                location.reload();
                              } catch (e: unknown) {
                                const err = e as { message?: string };
                                alert(`失敗：${err?.message}`);
                              }
                            }}
                            className="inline-flex items-center gap-2 px-5 py-2.5 bg-rose-500 text-white rounded-full font-bold text-sm hover:bg-rose-600 transition-colors"
                          >
                            <RefreshCw className="w-4 h-4" /> 全部重新解析
                          </button>
                          {/* 失敗詳情已顯示於左側資料列表（同頁），不再連結至已廢除的 /account/resource-library */}
                        </>
                      ) : documents.some(d => d.status === 'PROCESSING') ? (
                        // 情境 3：處理中
                        <>
                          <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                          <p className="text-lg text-slate-700 font-bold mb-2">AI 正在解析學習資源</p>
                          <ul className="text-xs text-slate-500 mb-3 text-left space-y-1 inline-block">
                            {documents.filter(d => d.status === 'PROCESSING').slice(0, 3).map(d => (
                              <li key={d.id} className="truncate max-w-[280px]">⚙️ {d.title}</li>
                            ))}
                          </ul>
                          <p className="text-xs text-slate-400 mt-2">
                            ⏰ 預估約 1-3 分鐘，離開頁面後仍會繼續處理。每 5 秒自動更新。
                          </p>
                        </>
                      ) : (
                        // 情境 4：資源已就緒但尚未生成知識樹
                        <>
                          <div className="text-5xl mb-3">🌱</div>
                          <p className="text-lg text-slate-700 font-bold mb-2">知識樹尚未生成</p>
                          <p className="text-xs text-slate-500 mb-4">
                            已有 {documents.length} 份資源，AI 可幫你萃取結構化知識節點。
                          </p>
                          <button
                            onClick={async () => {
                              if (extracting || !activeSubjectId) return;
                              const activeSubject = subjects.find(s => s.id === activeSubjectId);
                              const targetSubjectId = activeSubject?.subjectId || activeSubjectId;
                              setExtracting(true);
                              setExtractResult(null);
                              try {
                                const res = await knowledgeService.extractKnowledgeTree(targetSubjectId);
                                const created = (res as Record<string, number>).nodes_created || 0;
                                setExtractResult(`✅ 萃取完成：${created} 個知識節點`);
                                const mapRes = await knowledgeService.getMap(targetSubjectId) as Record<string, unknown>;
                                setNodes((mapRes.nodes || []) as KnowledgeNode[]);
                                setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
                              } catch (err) {
                                const msg = err instanceof Error ? err.message : String(err);
                                setExtractResult(`❌ 萃取失敗：${msg}`);
                              } finally {
                                setExtracting(false);
                              }
                            }}
                            disabled={extracting}
                            className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 text-white rounded-full font-bold text-sm hover:bg-emerald-600 transition-colors disabled:opacity-50"
                          >
                            <RefreshCw className={`w-4 h-4 ${extracting ? 'animate-spin' : ''}`} />
                            {extracting ? '萃取中...' : '🤖 萃取知識樹'}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ) : graphView === 'force' ? (
                  <ForceGraph nodes={graphNodes} onNodeClick={handleNodeClick}
                    selectedNodeId={selectedNodeDetail ? (selectedNodeDetail as unknown as Record<string, unknown>).node_id as string || selectedNodeDetail?.node?.id || null : null}
                    width={800} height={500} searchQuery={searchQuery} />
                ) : (
                  <div className="h-full overflow-y-auto p-3">
                    <MindMapTree nodes={mindMapNodes}
                      selectedNodeId={selectedNodeDetail ? (selectedNodeDetail as unknown as Record<string, unknown>).node_id as string || selectedNodeDetail?.node?.id || null : null}
                      onNodeClick={handleNodeClick} searchQuery={searchQuery} />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ── RIGHT: 節點詳情（4-Tab） ── */}
          {(showRightPanel || (isMobile && mobileDrawer === 'right')) && (() => {
            const nodeId = selectedNodeDetail ? ((selectedNodeDetail as unknown as Record<string, unknown>).node_id as string) || selectedNodeDetail.node?.id || null : null;
            const nodeLabel = selectedNodeDetail?.node?.label || null;

            const infoSlot = loadingDetail ? (
              <div className="p-3 flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : selectedNodeDetail ? (
              <div>
                <ScaffoldReplayCard
                  nodeId={nodeId}
                  masteryLevel={selectedNodeDetail.node?.masteryLevel}
                  isPro={isProPlus || subscriptionTier === 'PRO_199'}
                />
                {(() => {
                  // Spec 03b §「練習/測驗按鈕應依節點題目可用性決定啟用狀態」
                  // 從 mindMapNodes 找出當前節點的 available_questions
                  const findAvail = (list: MindMapNode[]): number | null => {
                    for (const n of list) {
                      if (n.id === nodeId) return n.available_questions ?? 0;
                      if (n.children?.length) {
                        const r = findAvail(n.children);
                        if (r !== null) return r;
                      }
                    }
                    return null;
                  };
                  const avail = nodeId ? (findAvail(mindMapNodes) ?? 0) : 0;
                  const noQ = avail === 0;
                  return (
                    <div className="px-3 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-blue-500" />
                      <h3 className="text-xs font-bold text-slate-700 truncate">{nodeLabel || '節點說明'}</h3>
                      {noQ ? (
                        <span className="ml-auto text-[10px] text-slate-300 cursor-not-allowed whitespace-nowrap" title="此節點目前無可用題目">練習</span>
                      ) : (
                        <button onClick={() => { const nname = nodeLabel || ''; router.push(`/practice?nodeId=${nodeId}&nodeName=${encodeURIComponent(nname)}`); }} className="ml-auto text-[10px] text-blue-600 font-medium hover:text-blue-700 whitespace-nowrap">練習</button>
                      )}
                      {noQ ? (
                        <span className="text-[10px] text-slate-300 cursor-not-allowed whitespace-nowrap" title="此節點目前無可用題目">測驗</span>
                      ) : (
                        <button onClick={() => { router.push(`/exam/setup?nodeId=${nodeId}`); }} className="text-[10px] text-emerald-600 font-medium hover:text-emerald-700 whitespace-nowrap">測驗</button>
                      )}
                    </div>
                  );
                })()}
                <div className="px-3 py-2">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold border ${selectedNodeDetail.node?.masteryLevel === 'mastered' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : selectedNodeDetail.node?.masteryLevel === 'partial' ? 'bg-amber-50 text-amber-700 border-amber-200' : selectedNodeDetail.node?.masteryLevel === 'weak' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                      {selectedNodeDetail.node?.masteryLevel === 'mastered' ? '精通' : selectedNodeDetail.node?.masteryLevel === 'partial' ? '部分' : selectedNodeDetail.node?.masteryLevel === 'weak' ? '弱' : '未測'}
                    </div>
                    <div className="flex items-center gap-1 text-[10px] text-slate-400">
                      {selectedNodeDetail.citationSource?.type === 'youtube' ? <Youtube className="h-3 w-3 text-red-500" /> : <FileText className="h-3 w-3 text-blue-400" />}
                      {selectedNodeDetail.citationSource?.type === 'youtube' ? `${Math.floor((selectedNodeDetail.citationSource?.timestampStart || 0) / 60)}:${String((selectedNodeDetail.citationSource?.timestampStart || 0) % 60).padStart(2, '0')}` : `頁 ${selectedNodeDetail.citationSource?.page || '-'}`}
                    </div>
                  </div>
                  {selectedNodeDetail.citationSource?.type === 'youtube' && selectedNodeDetail.citationSource?.sourceUrl && (
                    <div className="aspect-video bg-black rounded-lg overflow-hidden mb-2">
                      <iframe src={`https://www.youtube.com/embed/${extractYouTubeId(selectedNodeDetail.citationSource?.sourceUrl)}?start=${selectedNodeDetail.citationSource?.timestampStart || 0}&autoplay=0`} className="w-full h-full" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen title="YouTube" />
                    </div>
                  )}
                  {/* ── 概念說明 ── */}
                  {(selectedNodeDetail.citationText || selectedNodeDetail.sourceText) && !(selectedNodeDetail.citationText || selectedNodeDetail.sourceText || '').includes('無原文摘要') ? (
                    <div className="prose prose-slate prose-xs max-w-none">
                      <div className="whitespace-pre-line text-[11px] text-slate-600 leading-relaxed">
                        {renderMarkdown(selectedNodeDetail.citationText || selectedNodeDetail.sourceText || '')}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2 mt-1">
                      <p className="text-[11px] text-slate-500">📍 此關卡尚未解鎖——練習題目後說明文字將自動生成。</p>
                      <div className="flex flex-wrap gap-1.5">
                        <button onClick={() => { const nname = nodeLabel || ''; router.push(`/practice?nodeId=${nodeId}&nodeName=${encodeURIComponent(nname)}`); }} className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-[10px] border border-emerald-200 hover:bg-emerald-100">
                          📝 節點練習
                        </button>
                        <button onClick={() => { setActiveNodeTab('coach'); setChatInput('用簡單的話解釋'); }} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-[10px] border border-blue-200 hover:bg-blue-100">
                          💡 AI 教練解釋
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                {/* ── 學習鷹架（整合於節點資訊，消除分散注意力） ── */}
                <div className="border-t border-slate-100">
                  <div className="px-3 pt-2 pb-1 flex items-center gap-1.5">
                    <BookOpen className="h-3 w-3 text-emerald-500" />
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">學習鷹架</span>
                  </div>
                  <ScaffoldMaterial
                    nodeId={nodeId}
                    fallbackResourceId={focusResourceId || selectedDocId || (selectedNodeDetail?.node as { documentId?: string })?.documentId || null}
                    isPro={isProPlus || subscriptionTier === 'PRO_199'}
                    onUpgradeClick={() => router.push('/account')}
                  />
                </div>
              </div>
            ) : (
              <div className="px-3 py-4 text-center text-slate-400 text-xs">
                <BookOpen className="h-5 w-5 mx-auto mb-1 text-slate-300" />
                點擊圖譜節點查看說明
              </div>
            );

            const notebookSlot = (
              <ScaffoldNotebook
                nodeId={nodeId}
                fallbackResourceId={focusResourceId || selectedDocId || (selectedNodeDetail?.node as { documentId?: string })?.documentId || null}
                nodeLabel={nodeLabel}
                isPro={isProPlus || subscriptionTier === 'PRO_199'}
                onUpgradeClick={() => router.push('/account')}
              />
            );

            const coachSlot = (
              <div className="h-full flex flex-col overflow-hidden">
                {/* AI 教練模式切換列 */}
                <div className="px-3 py-2 flex items-center gap-2 border-b border-slate-100 bg-slate-50/50 shrink-0">
                  <button
                    onClick={() => setShowOrphanCoach(false)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold transition-colors ${
                      !showOrphanCoach
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'text-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    <MessageCircle className="h-3 w-3" />
                    問答
                  </button>
                  <button
                    onClick={() => { if (nodeId) setShowOrphanCoach(true); }}
                    disabled={!nodeId}
                    className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-semibold transition-colors ${
                      showOrphanCoach
                        ? 'bg-violet-100 text-violet-700'
                        : 'text-slate-400 hover:bg-slate-100'
                    } disabled:opacity-40 disabled:cursor-not-allowed`}
                    title="蘇格拉底引導模式：AI 透過提問幫你探索未知節點"
                  >
                    <Sparkles className="h-3 w-3" />
                    蘇格拉底
                  </button>
                  {!showOrphanCoach && isPro199 && (<span className="ml-auto text-[9px] text-amber-500 flex items-center gap-0.5"><Lock className="h-2.5 w-2.5" /> PRO_PLUS 專屬</span>)}
                  {!showOrphanCoach && !isProPlus && !isPro199 && (<span className="ml-auto text-[9px] text-slate-400">剩 {freeQueriesLeft}/3</span>)}
                </div>

                {/* 蘇格拉底 AI 教練面板 */}
                {showOrphanCoach && nodeId ? (
                  <OrphanCoachPanel
                    nodeId={nodeId}
                    nodeName={nodeLabel || '知識節點'}
                    onClose={() => setShowOrphanCoach(false)}
                    onSwitchToQuestion={(questionId) => {
                      router.push(`/practice?questionId=${questionId}`);
                    }}
                  />
                ) : showOrphanCoach && !nodeId ? (
                  <div className="flex-1 flex items-center justify-center">
                    <p className="text-xs text-slate-400">請先選擇一個知識節點</p>
                  </div>
                ) : (
                  // 標準問答 AI 教練（原有邏輯）
                  <>
                {!isPro199 && (isProPlus || freeQueriesLeft > 0) && selectedNodeDetail && (
                  <div className="px-2 py-1.5 flex flex-wrap gap-1 shrink-0 border-b border-slate-50">
                    {quickChips.map(chip => (<button key={chip} onClick={() => setChatInput(chip)} className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] border border-emerald-200 hover:bg-emerald-100 transition-colors">{chip}</button>))}
                  </div>
                )}
                <div className="flex-1 overflow-y-auto px-2 py-2 space-y-2">
                  {chatMessages.length === 0 && !isPro199 && selectedNodeDetail && (<div className="text-center py-4 text-[10px] text-slate-400">對所選節點提問，AI 教練為你解答</div>)}
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`flex gap-1.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                      <div className={`h-5 w-5 rounded-full flex items-center justify-center shrink-0 text-[9px] ${msg.role === 'ai' ? 'bg-emerald-100' : 'bg-slate-200'}`}>
                        {msg.role === 'ai' ? <MessageCircle className="h-3 w-3 text-emerald-600" /> : <span className="font-bold text-slate-600">U</span>}
                      </div>
                      <div className={`max-w-[85%] p-2 rounded-xl text-xs leading-relaxed ${msg.role === 'ai' ? 'bg-white border border-slate-200 text-slate-700 rounded-tl-none' : 'bg-emerald-500 text-white rounded-tr-none whitespace-pre-line'}`}>
                        {msg.role === 'ai' ? (
                          <div className="prose prose-xs max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-strong:text-slate-900 prose-code:text-emerald-700 prose-code:bg-emerald-50 prose-code:px-1 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
                            <MathContent>{msg.content}</MathContent>
                          </div>
                        ) : msg.content}
                      </div>
                    </div>
                  ))}
                  {chatLoading && (<div className="flex gap-1.5"><div className="h-5 w-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0"><MessageCircle className="h-3 w-3 text-emerald-600" /></div><div className="bg-white border border-slate-200 p-2 rounded-xl rounded-tl-none"><div className="flex gap-1"><div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" /><div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.1s]" /><div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.2s]" /></div></div></div>)}
                  {isPro199 && (<div className="p-3 backdrop-blur-md bg-white/50 border border-white/50 text-center rounded-xl"><Lock className="h-5 w-5 text-indigo-500 mx-auto mb-1" /><p className="text-[10px] text-slate-500 mb-2">AI 教練為 PRO_PLUS 專屬</p><Link href="/account" className="inline-flex items-center gap-1 bg-emerald-500 text-white px-3 py-1 rounded-lg text-[10px] font-bold hover:bg-emerald-600">升級 (NT$399/月)</Link></div>)}
                  {!isProPlus && !isPro199 && freeQueriesLeft <= 0 && (<div className="p-3 backdrop-blur-md bg-white/50 border border-white/50 text-center rounded-xl"><Lock className="h-5 w-5 text-indigo-500 mx-auto mb-1" /><p className="text-[10px] text-slate-500 mb-2">已達免費上限</p><Link href="/account" className="inline-flex items-center gap-1 bg-emerald-500 text-white px-3 py-1 rounded-lg text-[10px] font-bold hover:bg-emerald-600">解鎖無限 AI 教練</Link></div>)}
                  <div ref={chatEndRef} />
                </div>
                <div className="px-2 pb-2 shrink-0">
                  <div className="relative">
                    <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSendChat()} placeholder={isPro199 ? 'PRO_PLUS 專屬' : !isProPlus && freeQueriesLeft <= 0 ? '已達上限' : '提問...'} className="w-full pl-3 pr-8 py-1.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 text-xs disabled:opacity-50" disabled={chatLoading || isPro199 || (!isProPlus && freeQueriesLeft <= 0) || !selectedNodeDetail} />
                    <button onClick={() => handleSendChat()} disabled={chatLoading || !chatInput.trim() || isPro199 || (!isProPlus && freeQueriesLeft <= 0) || !selectedNodeDetail} className="absolute right-1 top-1/2 -translate-y-1/2 h-5 w-5 bg-emerald-500 text-white rounded flex items-center justify-center hover:bg-emerald-600 transition-colors disabled:opacity-50"><Send className="h-3 w-3" /></button>
                  </div>
                </div>
                </>
                )}
              </div>
            );

            return (
              <div className={`${isMobile ? 'absolute right-0 top-0 bottom-0 z-30 w-[85vw] max-w-[360px] shadow-xl' : 'w-[320px] lg:w-[360px]'} shrink-0 border-l border-slate-200 bg-white`}>
                {isMobile && (
                  <button onClick={() => setMobileDrawer(null)} className="absolute top-2 right-2 z-10 p-1 rounded hover:bg-slate-100">
                    <X className="h-4 w-4 text-slate-400" />
                  </button>
                )}
                <NodeDetailPanel
                  nodeId={nodeId}
                  nodeLabel={nodeLabel}
                  activeTab={activeNodeTab}
                  onTabChange={setActiveNodeTab}
                  infoSlot={infoSlot}
                  notebookSlot={notebookSlot}
                  coachSlot={coachSlot}
                />
              </div>
            );
          })()}

        </div>
      </div>

      {/* Hard Delete Confirmation Modal */}
      {deleteError && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-rose-50 border border-rose-200 rounded-xl px-4 py-2 text-sm text-rose-700 shadow-lg">
          刪除失敗：{deleteError}
          <button onClick={() => setDeleteError(null)} className="ml-3 text-rose-400 hover:text-rose-600">x</button>
        </div>
      )}
      <HardDeleteConfirmModal
        open={deleteModalOpen}
        onClose={() => { setDeleteModalOpen(false); setDeleteConfirmId(null); setDeleteError(null); }}
        onConfirm={handleConfirmHardDelete}
        title="永久刪除此教材"
        entityName={documents.find(d => d.id === deleteConfirmId)?.title ?? deleteConfirmId ?? ''}
        cascadeCount={deletePreviewLoading ? {} : deletePreviewCascade}
        loading={deletePreviewLoading || deleteConfirmLoading}
      />
    </>
  );
}

/** Simple markdown-like renderer for citation text */
function renderMarkdown(text: string) {
  if (!text) return null;
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;
    // H1
    if (trimmed.startsWith('# ')) return <h2 key={i} className="text-xl font-bold text-slate-900 mt-4 mb-2">{trimmed.slice(2)}</h2>;
    // H2
    if (trimmed.startsWith('## ')) return <h3 key={i} className="text-lg font-semibold text-slate-800 mt-3 mb-1.5">{trimmed.slice(3)}</h3>;
    // H3
    if (trimmed.startsWith('### ')) return <h4 key={i} className="text-base font-semibold text-slate-700 mt-2 mb-1">{trimmed.slice(4)}</h4>;
    // Bullet
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) return <li key={i} className="ml-4 list-disc text-sm text-slate-700">{renderInline(trimmed.slice(2))}</li>;
    // Numbered
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) return <li key={i} className="ml-4 list-decimal text-sm text-slate-700">{renderInline(numMatch[2])}</li>;
    // Blockquote
    if (trimmed.startsWith('> ')) return <blockquote key={i} className="border-l-3 border-emerald-400 pl-3 italic text-slate-600 my-2 text-sm">{renderInline(trimmed.slice(2))}</blockquote>;
    // Regular paragraph
    return <p key={i} className="text-sm text-slate-700 mb-1">{renderInline(trimmed)}</p>;
  });
}

/** Render inline markdown: **bold**, *italic*, `code` */
function renderInline(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={i} className="font-bold">{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*')) return <em key={i} className="italic">{part.slice(1, -1)}</em>;
    if (part.startsWith('`') && part.endsWith('`')) return <code key={i} className="bg-slate-100 px-1 py-0.5 rounded text-xs font-mono text-rose-600">{part.slice(1, -1)}</code>;
    return <span key={i}>{part}</span>;
  });
}

/** Extract YouTube video ID from URL */
function extractYouTubeId(url: string): string {
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?#]+)/);
  return match?.[1] ?? '';
}

export default function KnowledgeBasePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-gray-400">載入中...</div>}>
      <KnowledgeBasePageInner />
    </Suspense>
  );
}
