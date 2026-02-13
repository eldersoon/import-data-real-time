'use client';

import { Menu } from 'antd';
import { UploadOutlined, UnorderedListOutlined, CarOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export const Navigation: React.FC = () => {
  const pathname = usePathname();

  const getSelectedKey = () => {
    if (pathname?.startsWith('/upload')) return 'upload';
    if (pathname?.startsWith('/jobs')) return 'jobs';
    if (pathname?.startsWith('/vehicles')) return 'vehicles';
    return 'upload';
  };

  return (
    <Menu
      mode="inline"
      selectedKeys={[getSelectedKey()]}
      items={[
        {
          key: 'upload',
          icon: <UploadOutlined />,
          label: <Link href="/upload">Upload</Link>,
        },
        {
          key: 'jobs',
          icon: <UnorderedListOutlined />,
          label: <Link href="/jobs">Jobs</Link>,
        },
        {
          key: 'vehicles',
          icon: <CarOutlined />,
          label: <Link href="/vehicles">Veículos</Link>,
        },
      ]}
    />
  );
};
