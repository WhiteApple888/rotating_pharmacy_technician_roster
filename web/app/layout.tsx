import { Roboto, Roboto_Mono } from "next/font/google"
import type { Metadata } from "next"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

const roboto = Roboto({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "700"],
})

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: "RPT Monthly Roster Audit",
  description:
    "Validate monthly pharmacy technician roster shifts and staffing rules.",
  applicationName: "TTSH Pharmacy Operations",
  robots: {
    index: false,
    follow: false,
  },
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    type: "website",
    title: "RPT Monthly Roster Audit",
    description:
      "Validate monthly pharmacy technician roster shifts and staffing rules.",
    siteName: "TTSH Pharmacy Operations",
    images: [
      {
        url: "/opengraph-image.png",
        width: 1200,
        height: 630,
        alt: "RPT Monthly Roster Audit",
      },
    ],
  },
  other: {
    "theme-color": "#0f766e",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        "antialiased",
        robotoMono.variable,
        "font-sans",
        roboto.variable
      )}
    >
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  )
}
