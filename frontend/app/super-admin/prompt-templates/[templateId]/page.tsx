import PromptTemplateDetailPage from './client';

export function generateStaticParams() {
  return [{ templateId: 'detail' }];
}

export default function Page() {
  return <PromptTemplateDetailPage />;
}
