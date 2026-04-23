import CanvasClient from './client';

export function generateStaticParams() {
  return [{ id: 'detail' }];
}

export default function Page() {
  return <CanvasClient />;
}
