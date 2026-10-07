import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import Stepper from '../src/components/Stepper.vue'

const steps = [
  { key: 'general', label: 'Общие сведения', done: true },
  { key: 'items', label: 'Товары', done: true },
  { key: 'offers', label: 'Коммерческие предложения', done: false },
  { key: 'approvers', label: 'Согласующие', done: false, disabled: true },
]

describe('Stepper', () => {
  it('рендерит шаги, отмечает активный и пройденные', () => {
    const w = mount(Stepper, { props: { steps, modelValue: 1 } })
    const items = w.findAll('li.step')
    expect(items).toHaveLength(4)
    expect(items[1].classes()).toContain('active')
    expect(items[0].find('.circle').text()).toBe('✓')
    expect(items[1].find('.circle').text()).toBe('2') // активный показывает номер, а не галочку
    expect(items[1].find('button').attributes('aria-current')).toBe('step')
    expect(w.text()).toContain('Коммерческие предложения')
  })

  it('переключает шаг по клику', async () => {
    const w = mount(Stepper, { props: { steps, modelValue: 0 } })
    await w.findAll('li.step button')[2].trigger('click')
    expect(w.emitted('update:modelValue')).toEqual([[2]])
  })

  it('не переходит на недоступный и на текущий шаг', async () => {
    const w = mount(Stepper, { props: { steps, modelValue: 0 } })
    expect(w.findAll('li.step button')[3].attributes('disabled')).toBeDefined()
    await w.findAll('li.step button')[3].trigger('click')
    await w.findAll('li.step button')[0].trigger('click')
    expect(w.emitted('update:modelValue')).toBeUndefined()
  })
})
