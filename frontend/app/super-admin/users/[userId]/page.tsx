import UserDetailsPage from './client';

export const dynamicParams = false;

export function generateStaticParams() {
  return [
    { userId: 'usr_1' },
    { userId: 'usr_2' },
    { userId: 'usr_3' }
  ];
}

export default function Page() {
  return <UserDetailsPage />;
}
