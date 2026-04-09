'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FileText, Youtube, Search, Network, Send, Lock, Trash2, AlertTriangle, MessageCircle, ExternalLink, BookOpen } from 'lucide-react';
import { knowledgeService, subjectService, documentService } from '@/lib/api/services';
import type { Document, KnowledgeNode, GetNodeDetailResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';
import MindMapTree, { type MindMapNode } from '@/components/MindMapTree';
import ForceGraph, { type GraphNode } from '@/components/ForceGraph';
// react-resizable-panels removed — using plain flex layout

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
}

export default function KnowledgeBasePage() {
  const { isAuthenticated, loading: authLoading, onboardingCompleted, isProPlus, subscriptionTier } = useAuth();
  const isPro199 = subscriptionTier === 'PRO_199';
  const router = useRouter();
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
  const [freeQueriesLeft, setFreeQueriesLeft] = useState(isPro199 ? 0 : 3);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [graphView, setGraphView] = useState<'tree' | 'force'>('force');
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);

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
      if (res.subjects.length > 0) setActiveSubjectId(res.subjects[0].id);
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load knowledge map by active subject
  useEffect(() => {
    if (!activeSubjectId) return;
    setLoadingDocs(true);
    setLoadingDetail(false);
    setSelectedNodeDetail(null);
    setChatMessages([]);
    setFreeQueriesLeft(isPro199 ? 0 : 3);
    setDeleteConfirmId(null);

    const activeSubject = subjects.find(s => s.id === activeSubjectId);
    const targetSubjectId = activeSubject?.subjectId || activeSubjectId;

    knowledgeService.getMap(targetSubjectId).then((mapRes: Record<string, unknown>) => {
      const rawResources = (mapRes.resources || mapRes.documents || []) as Array<Record<string, string>>;
      const allDocuments: Document[] = rawResources.map(r => ({
        id: r.id,
        userId: '',
        title: r.name || r.title || '',
        sourceType: (r.type || r.resource_type || 'pdf') as Document['sourceType'],
        subjectId: targetSubjectId,
        sourceUrl: r.source_url || '',
        mcpParsedTranscriptUrl: null,
        status: 'COMPLETED' as Document['status'],
        fileSizeBytes: 0,
        visionRequired: false,
        createdAt: r.created_at || new Date().toISOString(),
      }));
      const allNodes = ((mapRes.nodes || []) as KnowledgeNode[]);
      setDocuments(allDocuments);
      setNodes(allNodes);
      setMindMapNodes((mapRes.nodes || []) as unknown as MindMapNode[]);
      setSelectedDocId(allDocuments[0]?.id ?? null);
      setLoadingDocs(false);
    }).catch(() => setLoadingDocs(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSubjectId]);

  const handleNodeClick = async (nodeId: string) => {
    setLoadingDetail(true);
    setChatMessages([]);
    setFreeQueriesLeft(isPro199 ? 0 : 3);
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

  // Auto-select first node
  useEffect(() => {
    if (nodes.length > 0 && !selectedNodeDetail) {
      handleNodeClick(nodes[0].children?.[0]?.id || nodes[0].id);
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
    if (!isProPlus) setFreeQueriesLeft(q => q - 1);
    try {
      const { apiClient } = await import('@/lib/api/client');
      const res = await apiClient.post<{ message: string }>(`/knowledge-map/nodes/${selectedNodeDetail?.node.id}/chat`, { message: text });
      setChatMessages(prev => [...prev, { role: 'ai', content: res.message }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'ai', content: '抱歉，暫時無法回覆。請稍後再試。' }]);
    }
    setChatLoading(false);
  };

  const handleDeleteDocument = async (docId: string) => {
    try { await documentService.delete(docId); } catch { /* silent */ }
    setDocuments(prev => prev.filter(d => d.id !== docId));
    setNodes(prev => prev.filter(n => n.documentId !== docId));
    setDeleteConfirmId(null);
    if (selectedDocId === docId) setSelectedDocId(null);
  };

  const sourceTypeIcons: Record<string, { icon: typeof FileText; color: string }> = {
    PDF: { icon: FileText, color: 'text-blue-500' },
    MARKDOWN: { icon: FileText, color: 'text-slate-500' },
    YOUTUBE_URL: { icon: Youtube, color: 'text-red-500' },
    IMAGE_MATH: { icon: FileText, color: 'text-purple-500' },
  };

  const quickChips = ['用簡單的話解釋', '給我一個例子', '轉成 1 題小測驗'];

  const showSubjectSwitcher = subjects.length > 0;
  const containerHeightClass = showSubjectSwitcher ? 'h-[calc(100vh-64px-48px)]' : 'h-[calc(100vh-64px)]';

  if (authLoading || !isAuthenticated || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      {showSubjectSwitcher && (
        <SubjectSwitcher
          subjects={subjects}
          activeSubjectId={activeSubjectId}
          onSwitch={setActiveSubjectId}
          onAddSubject={() => router.push('/onboarding')}
          allowAdd={false}
        />
      )}
      <div className={`flex-1 flex flex-col ${containerHeightClass} overflow-hidden bg-slate-50`}>
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-xl font-bold text-slate-900">知識庫</h1>
            <p className="text-xs text-slate-500">左側選擇資源，中間瀏覽內容，右側探索心智圖與 AI 教練</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜尋知識點..."
                className="pl-9 pr-4 py-1.5 rounded-full border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-48"
              />
            </div>
            <Link href="/dashboard" className="bg-emerald-500 text-white px-3 py-1.5 rounded-full text-sm font-medium hover:bg-emerald-600 transition-colors">
              + 新增資源
            </Link>
          </div>
        </header>

        {/* ===== THREE-COLUMN RESIZABLE LAYOUT ===== */}
        <div className="flex-1 flex overflow-hidden">

          {/* ── LEFT: Resource List ── */}
          {showLeftPanel && (
            <div className="w-[220px] shrink-0 border-r border-slate-200">
              <div className="h-full flex flex-col bg-white">
                <div className="p-3 border-b border-slate-100 flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-emerald-500" />
                  <h2 className="text-sm font-semibold text-slate-700">資料列表</h2>
                  <span className="ml-auto text-[10px] text-slate-400">{documents.length} 筆</span>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {loadingDocs ? (
                    [1, 2, 3].map(i => <div key={i} className="bg-slate-100 rounded-lg animate-pulse h-12" />)
                  ) : documents.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 text-xs">尚無資源</div>
                  ) : (
                    documents.filter(d => !searchQuery || d.title.toLowerCase().includes(searchQuery.toLowerCase())).map(doc => {
                      const isActive = doc.id === selectedDocId;
                      const { icon: Icon, color } = sourceTypeIcons[doc.sourceType] || sourceTypeIcons.PDF;
                      return (
                        <div key={doc.id} onClick={() => { setSelectedDocId(doc.id); const docNode = nodes.find(n => n.documentId === doc.id); if (docNode) handleNodeClick(docNode.children?.[0]?.id || docNode.id); }}
                          className={`group p-2.5 rounded-lg border cursor-pointer transition-colors ${isActive ? 'border-emerald-200 bg-emerald-50/50' : 'border-transparent hover:border-slate-200 hover:bg-slate-50'}`}>
                          <div className="flex items-center gap-2">
                            <Icon className={`h-4 w-4 shrink-0 ${color}`} />
                            <div className="flex-1 min-w-0"><h3 className="text-xs font-medium truncate">{doc.title}</h3><p className="text-[10px] text-slate-400">{doc.sourceType}</p></div>
                            <button onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(doc.id); }} className="text-slate-300 opacity-0 group-hover:opacity-100 hover:text-rose-500 transition-all shrink-0"><Trash2 className="h-3 w-3" /></button>
                          </div>
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
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-100 bg-slate-50/50 shrink-0">
                <div className="flex items-center gap-2">
                  <button onClick={() => setShowLeftPanel(!showLeftPanel)} className={`px-2 py-1 text-[10px] rounded font-medium transition-colors ${showLeftPanel ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                    {showLeftPanel ? '◀ 隱藏資料' : '▶ 資料列表'}
                  </button>
                  <div className="flex bg-slate-100 rounded-md p-0.5">
                    <button onClick={() => setGraphView('force')} className={`px-2 py-0.5 text-[10px] rounded font-medium ${graphView === 'force' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-400'}`}>🌐 圖譜</button>
                    <button onClick={() => setGraphView('tree')} className={`px-2 py-0.5 text-[10px] rounded font-medium ${graphView === 'tree' ? 'bg-white text-slate-700 shadow-sm' : 'text-slate-400'}`}>📋 列表</button>
                  </div>
                  <div className="flex items-center gap-2 text-[9px] text-slate-400 ml-2">
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />精熟</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-500" />部分</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" />弱</span>
                    <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-slate-300" />未測</span>
                  </div>
                </div>
                <button onClick={() => setShowRightPanel(!showRightPanel)} className={`px-2 py-1 text-[10px] rounded font-medium transition-colors ${showRightPanel ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                  {showRightPanel ? '說明 & AI ▶' : '◀ 說明 & AI'}
                </button>
              </div>
              {/* Graph */}
              <div className="flex-1 overflow-hidden">
                {graphView === 'force' ? (
                  <ForceGraph nodes={graphNodes} onNodeClick={handleNodeClick}
                    selectedNodeId={selectedNodeDetail ? (selectedNodeDetail as unknown as Record<string, unknown>).node_id as string || selectedNodeDetail?.node?.id || null : null}
                    width={800} height={500} />
                ) : (
                  <div className="h-full overflow-y-auto p-3">
                    <MindMapTree nodes={mindMapNodes}
                      selectedNodeId={selectedNodeDetail ? (selectedNodeDetail as unknown as Record<string, unknown>).node_id as string || selectedNodeDetail?.node?.id || null : null}
                      onNodeClick={handleNodeClick} />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ── RIGHT: 節點說明 + AI 教練 ── */}
          {showRightPanel && (
            <div className="w-[320px] shrink-0 border-l border-slate-200">
              <div className="h-full flex flex-col bg-white">

                {/* ━━ 上：節點說明 ━━ */}
                <div className={`${selectedNodeDetail ? 'max-h-[50%]' : ''} shrink-0 border-b border-slate-200 overflow-y-auto`}>
                  {loadingDetail ? (
                    <div className="p-3 flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                  ) : selectedNodeDetail ? (
                    <div>
                      <div className="px-3 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
                        <FileText className="h-3.5 w-3.5 text-blue-500" />
                        <h3 className="text-xs font-bold text-slate-700 truncate">{selectedNodeDetail.node?.label || '節點說明'}</h3>
                        <button onClick={() => { const nid = (selectedNodeDetail as unknown as Record<string, unknown>)?.node_id as string || selectedNodeDetail?.node?.id || ''; router.push(`/exam/setup?nodeId=${nid}`); }} className="ml-auto text-[10px] text-emerald-600 font-medium hover:text-emerald-700 whitespace-nowrap">生成測驗</button>
                      </div>
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
                        {(selectedNodeDetail.citationText || selectedNodeDetail.sourceText) && !(selectedNodeDetail.citationText || selectedNodeDetail.sourceText || '').includes('無原文摘要') ? (
                          <div className="prose prose-slate prose-xs max-w-none">
                            <div className="whitespace-pre-line text-[11px] text-slate-600 leading-relaxed">
                              {renderMarkdown(selectedNodeDetail.citationText || selectedNodeDetail.sourceText || '')}
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-2 mt-1">
                            <p className="text-[11px] text-slate-500">此節點尚無詳細說明文字。</p>
                            <div className="flex flex-wrap gap-1.5">
                              <button onClick={() => { const nid = (selectedNodeDetail as unknown as Record<string, unknown>)?.node_id as string || selectedNodeDetail?.node?.id || ''; router.push(`/exam/setup?nodeId=${nid}`); }} className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-[10px] border border-emerald-200 hover:bg-emerald-100">
                                📝 生成練習題
                              </button>
                              <button onClick={() => setChatInput('用簡單的話解釋')} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-[10px] border border-blue-200 hover:bg-blue-100">
                                💡 AI 教練解釋
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="px-3 py-4 text-center text-slate-400 text-xs">
                      <BookOpen className="h-5 w-5 mx-auto mb-1 text-slate-300" />
                      點擊圖譜節點查看說明
                    </div>
                  )}
                </div>

                {/* ━━ 下：AI 教練 ━━ */}
                <div className="flex-1 flex flex-col overflow-hidden">
                  <div className="px-3 py-2 flex items-center gap-2 border-b border-slate-100 bg-slate-50/50 shrink-0">
                    <MessageCircle className="h-3.5 w-3.5 text-emerald-500" />
                    <h3 className="text-xs font-bold text-slate-700">AI 教練</h3>
                    {isPro199 && (<span className="ml-auto text-[9px] text-amber-500 flex items-center gap-0.5"><Lock className="h-2.5 w-2.5" /> PRO_PLUS 專屬</span>)}
                    {!isProPlus && !isPro199 && (<span className="ml-auto text-[9px] text-slate-400">剩 {freeQueriesLeft}/3</span>)}
                  </div>
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
                        <div className={`max-w-[85%] p-2 rounded-xl text-xs leading-relaxed whitespace-pre-line ${msg.role === 'ai' ? 'bg-white border border-slate-200 text-slate-700 rounded-tl-none' : 'bg-emerald-500 text-white rounded-tr-none'}`}>{msg.content}</div>
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
                </div>

              </div>
            </div>
          )}

        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl p-6 max-w-md mx-4 shadow-2xl border border-rose-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
                <AlertTriangle className="h-5 w-5 text-rose-600" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">確定刪除此教材？</h3>
            </div>
            <p className="text-sm text-slate-600 mb-6 leading-relaxed">
              刪除此教材將同步移除心智圖上的關聯節點。<strong className="text-rose-700">此動作無法復原。</strong>
            </p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setDeleteConfirmId(null)} className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 border border-slate-200 hover:bg-slate-50">取消</button>
              <button onClick={() => handleDeleteDocument(deleteConfirmId)} className="px-4 py-2 rounded-lg text-sm font-bold text-white bg-rose-600 hover:bg-rose-700">確定刪除</button>
            </div>
          </div>
        </div>
      )}
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
