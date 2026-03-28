import UserDetailsPage from './client';

export function generateStaticParams() {
  return [{ userId: 'detail' }];
}

export default function Page() {
  return <UserDetailsPage />;
}
