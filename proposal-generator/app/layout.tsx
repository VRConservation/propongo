import { HelpProvider } from "@/contexts/help-context"

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <HelpProvider>{children}</HelpProvider>
      </body>
    </html>
  )
}


import './globals.css'

export const metadata = {
      generator: 'v0.dev'
    };
