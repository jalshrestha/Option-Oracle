'use client'

import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn('prose-chat', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          a: ({ href, children, node: _node, ...props }) => {
            const safeHref = href && /^(https?:|mailto:)/i.test(href) ? href : undefined
            return (
              <a
                href={safeHref}
                target={safeHref?.startsWith('http') ? '_blank' : undefined}
                rel={safeHref?.startsWith('http') ? 'noreferrer' : undefined}
                {...props}
              >
                {children}
              </a>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
