import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MarkdownRenderer } from './markdown-renderer'

describe('MarkdownRenderer', () => {
  it('renders markdown links, code, and GFM tables', () => {
    render(
      <MarkdownRenderer
        content={[
          '[OpenAI](https://openai.com)',
          '',
          '`AAPL` setup:',
          '',
          '| Symbol | Signal |',
          '| --- | --- |',
          '| AAPL | BUY |',
        ].join('\n')}
      />
    )

    expect(screen.getByRole('link', { name: 'OpenAI' })).toHaveAttribute(
      'href',
      'https://openai.com'
    )
    expect(screen.getAllByText('AAPL')).toHaveLength(2)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('sanitizes scripts and unsafe protocols', () => {
    const { container } = render(
      <MarkdownRenderer content={'<script>alert(1)</script>[bad](javascript:alert(1))'} />
    )

    expect(container.querySelector('script')).not.toBeInTheDocument()
    expect(container.querySelector('a')).not.toBeInTheDocument()
    expect(container).not.toHaveTextContent('alert')
  })
})
