import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'
import { DownOutlined, UpOutlined } from '@ant-design/icons'
import './MarkdownMessage.css'

function MarkdownMessage({ content, reasoningContent }) {
  const [reasoningExpanded, setReasoningExpanded] = useState(false)
  
  return (
    <div className="markdown-message">
      {reasoningContent && (
        <div className="reasoning-section">
          <div 
            className="reasoning-header" 
            onClick={() => setReasoningExpanded(!reasoningExpanded)}
            style={{ cursor: 'pointer', userSelect: 'none' }}
          >
            <span style={{ color: '#888', fontSize: '13px' }}>
              {reasoningExpanded ? <UpOutlined /> : <DownOutlined />}
              {' '}💭 思考过程
            </span>
          </div>
          {reasoningExpanded && (
            <div className="reasoning-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeSanitize]}
              >
                {reasoningContent}
              </ReactMarkdown>
            </div>
          )}
        </div>
      )}
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={{
          // 自定义代码块样式
          code({ node, inline, className, children, ...props }) {
            return inline ? (
              <code className="inline-code" {...props}>
                {children}
              </code>
            ) : (
              <pre className="code-block">
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            )
          },
          // 自定义链接样式
          a({ node, children, ...props }) {
            return (
              <a {...props} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            )
          },
          // 自定义图片样式
          img({ node, ...props }) {
            return (
              <img
                {...props}
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }}
                loading="lazy"
                alt={props.alt || '图片'}
              />
            )
          },
          // 自定义表格样式
          table({ node, children, ...props }) {
            return (
              <div style={{ overflowX: 'auto' }}>
                <table className="markdown-table" {...props}>
                  {children}
                </table>
              </div>
            )
          },
          // 自定义列表样式
          ul({ node, children, ...props }) {
            return <ul className="markdown-list" {...props}>{children}</ul>
          },
          ol({ node, children, ...props }) {
            return <ol className="markdown-list" {...props}>{children}</ol>
          },
          // 自定义引用样式
          blockquote({ node, children, ...props }) {
            return <blockquote className="markdown-blockquote" {...props}>{children}</blockquote>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownMessage
