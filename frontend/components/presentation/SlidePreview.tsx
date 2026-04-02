import { cn } from '@/lib/utils';
import type { Slide, SlideElement } from '@/types/presentation';

interface SlidePreviewProps {
  slide: Slide;
  isSelected?: boolean;
  scale?: number;
  onClick?: () => void;
}

function renderElement(element: SlideElement) {
  const style = {
    ...(element.style.color && { color: element.style.color }),
    ...(element.style.backgroundColor && {
      backgroundColor: element.style.backgroundColor,
    }),
    ...(element.style.fontSize && { fontSize: element.style.fontSize }),
    ...(element.style.textAlign && {
      textAlign: element.style.textAlign as 'left' | 'center' | 'right',
    }),
  };

  switch (element.type) {
    case 'heading':
      return (
        <h2 key={element.id} style={style} className="font-bold text-xl mb-2">
          {String(element.content)}
        </h2>
      );
    case 'text':
      return (
        <p key={element.id} style={style} className="text-sm">
          {String(element.content)}
        </p>
      );
    case 'list':
      return (
        <ul key={element.id} style={style} className="list-disc list-inside text-sm space-y-1">
          {(Array.isArray(element.content)
            ? element.content
            : [element.content]
          ).map((item, i) => (
            <li key={i}>{String(item)}</li>
          ))}
        </ul>
      );
    case 'quote':
      return (
        <blockquote
          key={element.id}
          style={style}
          className="border-l-4 border-primary-400 pl-4 italic text-sm"
        >
          {String(element.content)}
        </blockquote>
      );
    case 'image':
      return (
        <div
          key={element.id}
          className="rounded-lg bg-slate-200 flex items-center justify-center h-24 text-slate-400 text-xs"
        >
          [Image]
        </div>
      );
    default:
      return (
        <div
          key={element.id}
          className="rounded bg-slate-100 p-2 text-xs text-slate-500"
        >
          [{element.type}]
        </div>
      );
  }
}

export function SlidePreview({
  slide,
  isSelected = false,
  scale = 1,
  onClick,
}: SlidePreviewProps) {
  const sortedElements = [...slide.elements].sort(
    (a, b) => a.order - b.order,
  );

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative rounded-lg border-2 bg-white overflow-hidden cursor-pointer transition-all',
        isSelected
          ? 'border-primary-500 shadow-lg'
          : 'border-slate-200 hover:border-slate-300 shadow-sm',
      )}
      style={{
        aspectRatio: '16/9',
        transform: `scale(${scale})`,
        transformOrigin: 'top left',
      }}
    >
      <div className="p-4 h-full flex flex-col gap-2">
        {slide.title && (
          <h3 className="font-semibold text-slate-900 text-sm truncate">
            {slide.title}
          </h3>
        )}
        <div className="flex-1 space-y-2 overflow-hidden">
          {sortedElements.slice(0, 4).map(renderElement)}
        </div>
      </div>

      {isSelected && (
        <div className="absolute inset-0 ring-2 ring-inset ring-primary-500 rounded-lg pointer-events-none" />
      )}
    </div>
  );
}
