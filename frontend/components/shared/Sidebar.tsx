'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  Plug,
  Palette,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/presentations',
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    label: 'Agents',
    href: '/settings/agents',
    icon: <Bot className="h-4 w-4" />,
  },
  {
    label: 'Connections',
    href: '/settings/connections',
    icon: <Plug className="h-4 w-4" />,
  },
  {
    label: 'Styles',
    href: '/settings/styles',
    icon: <Palette className="h-4 w-4" />,
  },
  {
    label: 'Profile',
    href: '/settings/profile',
    icon: <User className="h-4 w-4" />,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-slate-200 bg-white min-h-screen p-4">
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
