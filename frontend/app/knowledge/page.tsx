'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FileText, Youtube, Search, MoreVertical, LayoutGrid, List, Network, ArrowRight, Send, Lock, Trash2, AlertTriangle, ChevronRight, ChevronDown, MessageCircle, X } from 'lucide-react';
import { knowledgeService, subjectService } from '@/lib/api/services';
import type { Document, KnowledgeNode, GetNodeDetailResponse, UserSubject } from '@/types';
import { useAuth } from '@/lib/auth-context';
import SubjectSwitcher from '@/components/SubjectSwitcher';

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
  // Subject state (備考科目)
  const [subjects, setSubjects] = useState<UserSubject[]>([]);
  const [activeSubjectId, setActiveSubjectId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [freeQueriesLeft, setFreeQueriesLeft] = useState(isPro199 ? 0 : 3);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [mindMapCollapsed, setMindMapCollapsed] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load subjects + guard
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!onboardingCompleted) {
      router.replace('/onboarding');
      return;
    }

    subjectService.getUserSubjects().then(res => {
      setSubjects(res.subjects);
      if (res.subjects.length > 0) setActiveSubjectId(res.subjects[0].id);
    }).catch(() => {});
  }, [authLoading, isAuthenticated, onboardingCompleted, router]);

  // Load & filter knowledge map by active subject
  useEffect(() => {
    if (!activeSubjectId) return;

    setLoadingDocs(true);
    setLoadingDetail(false);
    setSelectedNodeDetail(null);
    setChatMessages([]);
    setChatInput('');
    setChatLoading(false);
    setFreeQueriesLeft(isPro199 ? 0 : 3);
    setDeleteConfirmId(null);
    setMindMapCollapsed(false);

    knowledgeService.getMap().then(mapRes => {
      const activeSubject = subjects.find(s => s.id === activeSubjectId);
      const targetSubjectId = activeSubject?.subjectId || activeSubjectId;
      const filteredDocuments = mapRes.documents.filter(d => d.subjectId === targetSubjectId);
      const docsById = Object.fromEntries(filteredDocuments.map(d => [d.id, d])) as Record<string, Document>;
      const filteredNodes = filterKnowledgeNodesBySubject(mapRes.nodes, docsById, targetSubjectId);

      setDocuments(filteredDocuments);
      setNodes(filteredNodes);
      setSelectedDocId(filteredDocuments[0]?.id ?? null);

      // Auto-expand first-level nodes
      setExpandedNodes(new Set(filteredNodes.map(n => n.id)));
      setLoadingDocs(false);
    }).catch(() => setLoadingDocs(false));
  }, [activeSubjectId]);

  const handleNodeClick = async (nodeId: string) => {
    setLoadingDetail(true);
    setChatMessages([]);
    setFreeQueriesLeft(isPro199 ? 0 : 3);
    const detail = await knowledgeService.getNodeDetail(nodeId);
    setSelectedNodeDetail(detail);
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
    setDocuments(prev => prev.filter(d => d.id !== docId));
    setDeleteConfirmId(null);
    if (selectedDocId === docId) setSelectedDocId(null);
  };

  const toggleNodeExpand = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const sourceTypeIcons: Record<string, { icon: typeof FileText; color: string }> = {
    PDF: { icon: FileText, color: 'text-blue-500' },
    MARKDOWN: { icon: FileText, color: 'text-slate-500' },
    YOUTUBE_URL: { icon: Youtube, color: 'text-red-500' },
    IMAGE_MATH: { icon: FileText, color: 'text-purple-500' },
  };

  const quickChips = [
    '用五歲小孩聽得懂的方式解釋',
    '總結這三段重點',
    '轉成 1 題小測驗',
  ];

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
          <h1 className="text-xl font-bold text-slate-900">知識庫與心智圖</h1>
          <p className="text-xs text-slate-500">點擊右側節點導航，左側即時溯源與 AI 教練對話</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜尋知識點..."
              className="pl-9 pr-4 py-1.5 rounded-full border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 w-56"
            />
          </div>
          <Link href="/dashboard" className="bg-emerald-500 text-white px-3 py-1.5 rounded-full text-sm font-medium hover:bg-emerald-600 transition-colors">
            + 新增資源
          </Link>
        </div>
      </header>

      {/* Main Content Area - Restructured: Resource | Citation+AI Tutor | Mind Map */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left Panel: Resource List */}
        <div className="w-64 border-r border-slate-200 bg-white flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">已解析資源</h2>
            <div className="flex gap-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1 rounded transition-colors ${viewMode === 'grid' ? 'bg-slate-100 text-slate-700' : 'hover:bg-slate-100 text-slate-400'}`}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1 rounded transition-colors ${viewMode === 'list' ? 'bg-slate-100 text-slate-700' : 'hover:bg-slate-100 text-slate-400'}`}
              >
                <List className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className={`flex-1 overflow-y-auto p-2 ${viewMode === 'grid' ? 'grid grid-cols-2 gap-2 content-start' : 'space-y-1'}`}>
            {loadingDocs ? (
              [1, 2, 3].map(i => (
                <div key={i} className={`bg-slate-100 rounded-lg animate-pulse ${viewMode === 'grid' ? 'h-24' : 'h-14'}`} />
              ))
            ) : (
              documents.map(doc => {
                const isActive = doc.id === selectedDocId;
                const { icon: Icon, color } = sourceTypeIcons[doc.sourceType] || sourceTypeIcons.PDF;
                const isFailed = doc.status === 'FAILED';
                const isPending = doc.status === 'PENDING' || doc.status === 'PROCESSING';
                return (
                  <div
                    key={doc.id}
                    onClick={() => !isFailed && setSelectedDocId(doc.id)}
                    className={`group p-2.5 rounded-lg border cursor-pointer transition-colors relative ${
                      isActive ? 'border-emerald-200 bg-emerald-50/50' : 'border-transparent hover:border-slate-200 hover:bg-slate-50'
                    } ${isFailed ? 'opacity-60' : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="mt-0.5 bg-white p-1 rounded shadow-sm border border-slate-100">
                        <Icon className={`h-4 w-4 ${color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className={`text-xs font-medium truncate ${isActive ? 'text-slate-900' : 'text-slate-700'}`}>{doc.title}</h3>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          {isPending ? '解析中...' : isFailed ? '解析失敗' : doc.sourceType === 'YOUTUBE_URL' ? 'YouTube' : doc.sourceType}
                        </p>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeleteConfirmId(doc.id); }}
                        className="text-slate-300 opacity-0 group-hover:opacity-100 hover:text-rose-500 transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Ultra Upsell / Sync */}
          <div className="p-3 border-t border-slate-200 bg-slate-50">
            <div className="rounded-lg border border-indigo-100 bg-indigo-50 p-3 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-12 h-12 bg-indigo-500/10 rounded-bl-full"></div>
              <h4 className="text-xs font-bold text-indigo-900 mb-1">自動同步排程</h4>
              <p className="text-[10px] text-indigo-700/80 mb-2">連接 Notion 或 Google Drive</p>
              <Link href="/account" className="text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                解鎖 Ultra 版 <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        </div>

        {/* Center Panel: Citation & AI Tutor (Core Soul — 70-75%) */}
        <div className={`flex-1 bg-white flex flex-col overflow-hidden border-r border-slate-200 ${mindMapCollapsed ? '' : 'min-w-0'}`}>
          {loadingDetail ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="space-y-4 animate-pulse w-full max-w-2xl px-8">
                <div className="h-8 bg-slate-200 rounded w-1/3" />
                <div className="h-40 bg-slate-200 rounded" />
                <div className="h-60 bg-slate-200 rounded" />
              </div>
            </div>
          ) : selectedNodeDetail ? (
            <>
              {/* Upper: Dynamic Citation / Ground Truth */}
              <div className="flex-1 overflow-y-auto">
                <div className="max-w-3xl mx-auto px-8 py-6">
                  {/* Node Title & Mastery */}
                  <div className="mb-6">
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">{selectedNodeDetail.node.label}</h2>
                    <div className="flex items-center gap-3">
                      <div className={`inline-flex px-2 py-0.5 rounded text-xs font-bold border ${
                        selectedNodeDetail.node.masteryLevel === 'mastered' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        selectedNodeDetail.node.masteryLevel === 'partial' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        selectedNodeDetail.node.masteryLevel === 'weak' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                        'bg-slate-50 text-slate-500 border-slate-200'
                      }`}>
                        {selectedNodeDetail.node.masteryLevel === 'mastered' ? '已精通' :
                         selectedNodeDetail.node.masteryLevel === 'partial' ? '部分掌握' :
                         selectedNodeDetail.node.masteryLevel === 'weak' ? '需加強' : '未測驗'}
                      </div>
                      <button className="text-xs text-emerald-600 font-medium hover:text-emerald-700">
                        生成此節點測驗
                      </button>
                    </div>
                  </div>

                  {/* Citation Source Card */}
                  <div className="rounded-xl border border-slate-200 overflow-hidden mb-6">
                    <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">溯源定位</h4>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        {selectedNodeDetail.citationSource.type === 'youtube' ? (
                          <Youtube className="h-3 w-3 text-red-500" />
                        ) : (
                          <FileText className="h-3 w-3 text-blue-500" />
                        )}
                        {selectedNodeDetail.citationSource.documentTitle}
                        <span className="text-slate-400">
                          {selectedNodeDetail.citationSource.type === 'youtube'
                            ? ` ${Math.floor((selectedNodeDetail.citationSource.timestampStart || 0) / 60)}:${String((selectedNodeDetail.citationSource.timestampStart || 0) % 60).padStart(2, '0')}`
                            : ` p.${selectedNodeDetail.citationSource.page}`}
                        </span>
                      </div>
                    </div>

                    {/* YouTube Embed Player */}
                    {selectedNodeDetail.citationSource.type === 'youtube' && selectedNodeDetail.citationSource.sourceUrl && (
                      <div className="aspect-video bg-black">
                        <iframe
                          src={`https://www.youtube.com/embed/${extractYouTubeId(selectedNodeDetail.citationSource.sourceUrl)}?start=${selectedNodeDetail.citationSource.timestampStart || 0}&autoplay=0`}
                          className="w-full h-full"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                          title="YouTube citation"
                        />
                      </div>
                    )}

                    {/* Highlighted Citation Text */}
                    <div className="p-5 bg-yellow-50/40">
                      <p className="text-sm text-slate-700 leading-relaxed border-l-3 border-yellow-400 pl-4 italic">
                        <span className="bg-yellow-200/60 px-0.5">{selectedNodeDetail.citationText}</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Lower: AI Tutor Chat */}
                <div className="border-t border-slate-100 bg-slate-50/50">
                  <div className="max-w-3xl mx-auto px-8 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <MessageCircle className="h-4 w-4 text-emerald-500" />
                      <h4 className="text-sm font-bold text-slate-700">AI 教練對話</h4>
                      {isPro199 && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-amber-500 ml-auto font-medium">
                          <Lock className="h-3 w-3" />
                          AI 教練深度對話為 PRO_PLUS 專屬功能，升級解鎖
                        </span>
                      )}
                      {!isProPlus && !isPro199 && (
                        <span className="text-[10px] text-slate-400 ml-auto">免費額度剩餘 {freeQueriesLeft}/3</span>
                      )}
                    </div>

                    {/* Quick Action Chips — hidden for PRO_199 (no access at all) */}
                    {!isPro199 && (isProPlus || freeQueriesLeft > 0) && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {quickChips.map(chip => (
                          <button
                            key={chip}
                            onClick={() => setChatInput(chip)}
                            className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs border border-emerald-200 hover:bg-emerald-100 transition-colors"
                          >
                            {chip}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Chat Messages */}
                    <div className="space-y-3 max-h-80 overflow-y-auto mb-3">
                      {chatMessages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                          <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 ${
                            msg.role === 'ai' ? 'bg-emerald-100' : 'bg-slate-200'
                          }`}>
                            {msg.role === 'ai' ? (
                              <MessageCircle className="h-4 w-4 text-emerald-600" />
                            ) : (
                              <span className="text-xs font-bold text-slate-600">U</span>
                            )}
                          </div>
                          <div className={`max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                            msg.role === 'ai'
                              ? 'bg-white border border-slate-200 text-slate-700 rounded-tl-none'
                              : 'bg-emerald-500 text-white rounded-tr-none'
                          }`}>
                            {msg.content}
                          </div>
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="flex gap-3">
                          <div className="h-7 w-7 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                            <MessageCircle className="h-4 w-4 text-emerald-600" />
                          </div>
                          <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none">
                            <div className="flex gap-1">
                              <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" />
                              <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.1s]" />
                              <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.2s]" />
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Glassmorphism Paywall — PRO_199: immediate lock */}
                      {isPro199 && (
                        <div className="relative rounded-2xl overflow-hidden">
                          <div className="p-6 backdrop-blur-md bg-white/50 border border-white/50 text-center">
                            <div className="mx-auto h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center mb-3">
                              <Lock className="h-5 w-5 text-indigo-500" />
                            </div>
                            <h4 className="font-bold text-slate-900 mb-1">AI 教練深度對話為 PRO_PLUS 專屬功能</h4>
                            <p className="text-xs text-slate-500 mb-4">升級即可使用 Claude 3.5 終極教練，深度溯源探討</p>
                            <Link href="/account" className="inline-flex items-center gap-1 bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-emerald-600 transition-colors">
                              解鎖 Claude 3.5 終極教練 (NT$399/月)
                            </Link>
                          </div>
                        </div>
                      )}

                      {/* Glassmorphism Paywall — FREE: after 3 queries exhausted */}
                      {!isProPlus && !isPro199 && freeQueriesLeft <= 0 && (
                        <div className="relative rounded-2xl overflow-hidden">
                          <div className="p-6 backdrop-blur-md bg-white/50 border border-white/50 text-center">
                            <div className="mx-auto h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center mb-3">
                              <Lock className="h-5 w-5 text-indigo-500" />
                            </div>
                            <h4 className="font-bold text-slate-900 mb-1">已達免費追問上限</h4>
                            <p className="text-xs text-slate-500 mb-4">升級 PRO_PLUS 解鎖無限對話</p>
                            <Link href="/account" className="inline-flex items-center gap-1 bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-emerald-600 transition-colors">
                              解鎖 AI 教練 (NT$399/月)
                            </Link>
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    {/* Chat Input */}
                    <div className="relative">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSendChat()}
                        placeholder={isPro199 ? 'AI 教練深度對話為 PRO_PLUS 專屬功能' : !isProPlus && freeQueriesLeft <= 0 ? '已達免費追問上限，升級 PRO_PLUS 解鎖無限對話' : '我不懂這裡的意思，能給我實例嗎？'}
                        className="w-full pl-4 pr-12 py-2.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all text-sm disabled:opacity-50"
                        disabled={chatLoading || isPro199 || (!isProPlus && freeQueriesLeft <= 0)}
                      />
                      <button
                        onClick={() => handleSendChat()}
                        disabled={chatLoading || !chatInput.trim() || isPro199 || (!isProPlus && freeQueriesLeft <= 0)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 bg-emerald-500 text-white rounded-lg flex items-center justify-center hover:bg-emerald-600 transition-colors disabled:opacity-50"
                      >
                        <Send className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1.5 italic">
                      AI 生成內容僅供參考；點擊送出問題即表示已知悉法規政策。
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
              點擊右側心智圖節點以查看溯源原文與 AI 教練
            </div>
          )}
        </div>

        {/* Right Panel: Mind Map Navigator (25-30%) */}
        {!mindMapCollapsed && (
          <div className="w-80 bg-white flex flex-col shrink-0 border-l border-slate-100">
            <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Network className="h-4 w-4 text-emerald-500" /> 知識導航
              </h3>
              <button
                onClick={() => setMindMapCollapsed(true)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                收合
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3">
              {/* Tree-style mind map navigator */}
              {nodes.map(node => {
                const isExpanded = expandedNodes.has(node.id);
                const isActive = selectedNodeDetail?.node.id === node.id;
                const nodeMasteryText =
                  node.masteryLevel === 'mastered' ? 'text-emerald-600' :
                  node.masteryLevel === 'partial' ? 'text-amber-600' :
                  node.masteryLevel === 'weak' ? 'text-rose-600' :
                  'text-slate-400';
                const nodeMasteryBorder =
                  node.masteryLevel === 'mastered' ? 'border-emerald-200 bg-emerald-50/30' :
                  node.masteryLevel === 'partial' ? 'border-amber-200 bg-amber-50/30' :
                  node.masteryLevel === 'weak' ? 'border-rose-200 bg-rose-50/30' :
                  'border-slate-200 bg-slate-50/30';
                return (
                  <div key={node.id} className="mb-1">
                    <button
                      onClick={() => {
                        toggleNodeExpand(node.id);
                        handleNodeClick(node.id);
                      }}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                        isActive
                          ? `${nodeMasteryBorder} font-bold border`
                          : `hover:bg-slate-50`
                      }`}
                    >
                      {node.children && node.children.length > 0 ? (
                        isExpanded ? <ChevronDown className={`h-3.5 w-3.5 ${nodeMasteryText} shrink-0`} /> : <ChevronRight className={`h-3.5 w-3.5 ${nodeMasteryText} shrink-0`} />
                      ) : (
                        <div className="w-3.5 shrink-0" />
                      )}
                      <span className={`text-sm truncate ${isActive ? nodeMasteryText : nodeMasteryText}`}>{node.label}</span>
                    </button>

                    {/* Children */}
                    {isExpanded && node.children && node.children.length > 0 && (
                      <div className="ml-5 border-l border-slate-100 pl-2 mt-0.5">
                        {node.children.map(child => {
                          const childActive = selectedNodeDetail?.node.id === child.id;
                          const masteryDot =
                            child.masteryLevel === 'mastered' ? 'bg-emerald-400' :
                            child.masteryLevel === 'partial' ? 'bg-amber-400' :
                            child.masteryLevel === 'weak' ? 'bg-rose-400' :
                            'bg-slate-300';
                          const childMasteryText =
                            child.masteryLevel === 'mastered' ? 'text-emerald-600' :
                            child.masteryLevel === 'partial' ? 'text-amber-600' :
                            child.masteryLevel === 'weak' ? 'text-rose-600' :
                            'text-slate-400';
                          const childActiveBg =
                            child.masteryLevel === 'mastered' ? 'bg-emerald-50' :
                            child.masteryLevel === 'partial' ? 'bg-amber-50' :
                            child.masteryLevel === 'weak' ? 'bg-rose-50' :
                            'bg-slate-50';
                          return (
                            <button
                              key={child.id}
                              onClick={() => handleNodeClick(child.id)}
                              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-left transition-colors my-0.5 ${
                                childActive
                                  ? `${childActiveBg} ${childMasteryText} font-semibold`
                                  : `${childMasteryText} hover:bg-slate-50`
                              }`}
                            >
                              <div className={`w-2 h-2 rounded-full shrink-0 ${masteryDot}`} />
                              <span className="text-xs truncate">{child.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="p-3 border-t border-slate-100 bg-slate-50/50">
              <div className="flex items-center gap-3 text-[10px] text-slate-500">
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-400" /> 精熟</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-400" /> 部分</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-rose-400" /> 需加強</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-slate-300" /> 未測驗</span>
              </div>
            </div>
          </div>
        )}

        {/* Mind Map Collapsed Toggle */}
        {mindMapCollapsed && (
          <button
            onClick={() => setMindMapCollapsed(false)}
            className="w-10 bg-slate-50 border-l border-slate-200 flex items-center justify-center hover:bg-slate-100 transition-colors shrink-0"
            title="展開心智圖導航"
          >
            <Network className="h-4 w-4 text-slate-400" />
          </button>
        )}
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
              刪除此教材將同步移除心智圖上的關聯節點，並停止 AI 教練針對此範圍出題。<strong className="text-rose-700">此動作無法復原。</strong>
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleDeleteDocument(deleteConfirmId)}
                className="px-4 py-2 rounded-lg text-sm font-bold text-white bg-rose-600 hover:bg-rose-700 transition-colors"
              >
                確定刪除
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}

function filterKnowledgeNodesBySubject(
  roots: KnowledgeNode[],
  docsById: Record<string, Document>,
  subjectId: string
): KnowledgeNode[] {
  const filterNode = (node: KnowledgeNode): KnowledgeNode | null => {
    const nodeBelongs = docsById[node.documentId]?.subjectId === subjectId;
    const filteredChildren = node.children
      .map(child => filterNode(child))
      .filter((c): c is KnowledgeNode => c !== null);

    if (nodeBelongs || filteredChildren.length > 0) {
      return { ...node, children: filteredChildren };
    }
    return null;
  };

  return roots.map(root => filterNode(root)).filter((n): n is KnowledgeNode => n !== null);
}

/** Extract YouTube video ID from URL */
function extractYouTubeId(url: string): string {
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&?#]+)/);
  return match?.[1] ?? '';
}
