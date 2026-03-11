/**
 * Basic smoke test for the Sidebar component.
 * Verifies that all navigation links are rendered and the close button is present.
 */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Sidebar from '../components/Sidebar'

const NAV_LABELS = [
  'Dashboard',
  'Schedule',
  'Employees',
  'Jobs',
  'Reports',
  'Integrations',
  'Settings',
  'Help',
]

describe('Sidebar', () => {
  it('renders all navigation links when open', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />)

    for (const label of NAV_LABELS) {
      expect(screen.getByRole('link', { name: label })).toBeInTheDocument()
    }
  })

  it('calls onClose when the close button is clicked', async () => {
    const onClose = jest.fn()
    render(<Sidebar isOpen={true} onClose={onClose} />)

    await userEvent.click(screen.getByRole('button', { name: 'Close navigation' }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('renders the business selector placeholder', () => {
    render(<Sidebar isOpen={true} onClose={() => {}} />)
    expect(screen.getByRole('combobox', { name: 'Business' })).toBeInTheDocument()
  })
})
