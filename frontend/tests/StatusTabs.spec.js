import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import StatusTabs from '../src/components/StatusTabs.vue'

describe('StatusTabs', () => {
  const tabs = [{ key: 'draft', label: 'Черновики', count: 3 }, { key: 'all', label: 'Все', count: 10 }]

  it('показывает счётчики и выделяет активный таб', () => {
    const w = mount(StatusTabs, { props: { tabs, modelValue: 'all' } })
    const pills = w.findAll('.pill')
    expect(pills[0].find('.count').text()).toBe('3')
    expect(pills[1].classes()).toContain('active')
    expect(pills[0].classes()).not.toContain('active')
  })

  it('эмитит выбранный таб', async () => {
    const w = mount(StatusTabs, { props: { tabs, modelValue: 'all' } })
    await w.findAll('.pill')[0].trigger('click')
    expect(w.emitted('update:modelValue')).toEqual([['draft']])
  })
})
