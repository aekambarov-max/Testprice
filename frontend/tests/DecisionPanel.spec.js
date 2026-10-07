import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DecisionPanel from '../src/components/DecisionPanel.vue'

const analysis = (over = {}) => ({
  id: 7, status: 'on_approval_db', current_stage: 2, current_step_id: 42,
  available_actions: ['approve', 'rework'], ...over,
})

const mountPanel = (props) => mount(DecisionPanel, { props: { teleport: false, ...props }, attachTo: document.body })

describe('DecisionPanel (экран решения)', () => {
  it('не показывается, если пользователь не текущий исполнитель', () => {
    const w = mountPanel({ analysis: analysis({ available_actions: [] }), submit: vi.fn() })
    expect(w.find('[data-test="approve"]').exists()).toBe(false)
  })

  it('согласование: комментарий необязателен, передаётся id шага', async () => {
    const submit = vi.fn().mockResolvedValue()
    const w = mountPanel({ analysis: analysis(), submit })
    expect(w.find('[data-test="approve"]').text()).toBe('Согласовать')
    await w.find('[data-test="approve"]').trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(submit).toHaveBeenCalledWith('approve', '', 42)
    expect(w.find('[data-test="comment"]').exists()).toBe(false) // модальное окно закрыто
  })

  it('на этапе директора кнопка называется «Утвердить»', () => {
    const w = mountPanel({ analysis: analysis({ current_stage: 3 }), submit: vi.fn() })
    expect(w.find('[data-test="approve"]').text()).toBe('Утвердить')
  })

  it('возврат на доработку без комментария не отправляется', async () => {
    const submit = vi.fn()
    const w = mountPanel({ analysis: analysis(), submit })
    await w.find('[data-test="rework"]').trigger('click')
    await w.find('[data-test="comment"]').setValue('   ')
    await w.find('[data-test="confirm"]').trigger('click')
    expect(submit).not.toHaveBeenCalled()
    expect(w.find('[data-test="comment-error"]').text()).toContain('Укажите причину возврата')
  })

  it('возврат с комментарием отправляется', async () => {
    const submit = vi.fn().mockResolvedValue()
    const w = mountPanel({ analysis: analysis(), submit })
    await w.find('[data-test="rework"]').trigger('click')
    await w.find('[data-test="comment"]').setValue('  Нет обоснования цены ')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(submit).toHaveBeenCalledWith('rework', 'Нет обоснования цены', 42)
  })

  it('показывает ошибку сервера и оставляет окно открытым', async () => {
    const submit = vi.fn().mockRejectedValue(new Error('Шаг уже обработан. Обновите страницу.'))
    const w = mountPanel({ analysis: analysis(), submit })
    await w.find('[data-test="approve"]').trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(w.text()).toContain('Шаг уже обработан')
    expect(w.find('[data-test="comment"]').exists()).toBe(true)
  })
})
