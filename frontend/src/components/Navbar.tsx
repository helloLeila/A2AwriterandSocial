import { useState } from 'react';
import type { NotificationItem } from '../types';

interface Props {
  notifications?: NotificationItem[];
  onNotificationClick?: () => void;
}

const fallbackNotifications: NotificationItem[] = [
  {
    id: 'ambient-1',
    tag: '赞同',
    title: '知乎用户 54321 赞同了你的回答',
    excerpt: '大一到底要怎样做才能兼顾学习与社交？',
    time: '12 分钟前',
  },
  {
    id: 'ambient-2',
    tag: '互动',
    title: '小青 邀请你回答一个校园成长问题',
    excerpt: '大学期间如何平衡学业、社交与个人成长？',
    time: '今天',
  },
];

export default function Navbar({ notifications = [], onNotificationClick }: Props) {
  const [showNotifications, setShowNotifications] = useState(false);
  const items = notifications.length > 0 ? notifications : fallbackNotifications;
  const unreadCount = notifications.length || 1;

  return (
    <nav className="zhihu-nav">
      <div className="zhihu-nav-logo">知乎</div>
      <div className="zhihu-nav-links">
        <a href="#" className="active">关注</a>
        <a href="#">推荐</a>
        <a href="#">热榜</a>
        <a href="#">专栏</a>
        <a href="#">圈子</a>
        <a href="#">付费咨询</a>
        <a href="#">知学堂</a>
      </div>
      <div className="zhihu-nav-right">
        <div className="zhihu-nav-search">搜索你感兴趣的内容...</div>
        <button className="zhihu-nav-direct">直答</button>
        <button className="zhihu-nav-plus">+</button>
        <div className="zhihu-nav-notify-wrap">
          <button
            className="zhihu-nav-icon-btn"
            onClick={() => setShowNotifications((v) => !v)}
          >
            消息
            <span className="nav-badge">{unreadCount}</span>
          </button>
          {showNotifications && (
            <div className="notification-popover">
              <div className="notification-tabs">
                <button className="active">互动</button>
                <button>关注</button>
                <button>赞同</button>
              </div>
              <div className="notification-list">
                {items.map((item) => (
                  <button
                    key={item.id}
                    className="notification-item"
                    onClick={() => {
                      setShowNotifications(false);
                      onNotificationClick?.();
                    }}
                  >
                    <div className="notification-item-top">
                      <span>{item.tag}</span>
                      <time>{item.time}</time>
                    </div>
                    <div className="notification-title">{item.title}</div>
                    <div className="notification-excerpt">{item.excerpt}</div>
                  </button>
                ))}
              </div>
              <div className="notification-footer">
                <span>设置</span>
                <span>查看全部通知</span>
              </div>
            </div>
          )}
        </div>
        <button className="zhihu-nav-icon-btn">私信</button>
        <button className="zhihu-nav-icon-btn">创作中心</button>
        <div className="zhihu-nav-avatar">我</div>
      </div>
    </nav>
  );
}
