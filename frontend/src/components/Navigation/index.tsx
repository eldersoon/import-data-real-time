'use client';

import { Menu } from 'antd';
import { UploadOutlined, UnorderedListOutlined, CarOutlined, DatabaseOutlined, SettingOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEntities } from '@/lib/api/hooks/useEntities';
import type { MenuProps } from 'antd';
import { useMemo } from 'react';

// Icon mapping for common entity icons
const getIcon = (iconName?: string) => {
  // You can extend this with more icon mappings
  const iconMap: Record<string, React.ReactNode> = {
    database: <DatabaseOutlined />,
  };
  return iconName && iconMap[iconName] ? iconMap[iconName] : <DatabaseOutlined />;
};

export const Navigation: React.FC = () => {
  const pathname = usePathname();
  const { data: entities = [], isLoading } = useEntities(true); // Only visible entities

  const getSelectedKey = () => {
    if (pathname?.startsWith('/upload')) return 'upload';
    if (pathname?.startsWith('/jobs')) return 'jobs';
    if (pathname?.startsWith('/vehicles')) return 'vehicles';
    if (pathname?.startsWith('/admin/entities')) return 'admin-entities';
    if (pathname?.startsWith('/entities/')) {
      const tableName = pathname.split('/entities/')[1];
      return `entity-${tableName}`;
    }
    return 'upload';
  };

  const menuItems: MenuProps['items'] = useMemo(() => {
    const baseItems: MenuProps['items'] = [
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
      {
        type: 'divider',
      },
      {
        key: 'admin-entities',
        icon: <SettingOutlined />,
        label: <Link href="/admin/entities">Gerenciar Entidades</Link>,
      },
    ];

    // Add dynamic entity items
    const entityItems: MenuProps['items'] = entities.map((entity) => ({
      key: `entity-${entity.table_name}`,
      icon: getIcon(entity.icon),
      label: <Link href={`/entities/${entity.table_name}`}>{entity.display_name}</Link>,
    }));

    return [...baseItems, ...entityItems];
  }, [entities]);

  if (isLoading) {
    return <Menu mode="inline" items={[]} />;
  }

  return (
    <Menu
      mode="inline"
      selectedKeys={[getSelectedKey()]}
      items={menuItems}
    />
  );
};
