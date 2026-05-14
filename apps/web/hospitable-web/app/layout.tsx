import './globals.css'
import ClientLayout from '../components/ClientLayout'
import { AuthProvider } from '../lib/auth-store'

export const metadata = { title: 'Hospitable Web' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ClientLayout>{children}</ClientLayout>
        </AuthProvider>
      </body>
    </html>
  )
}
