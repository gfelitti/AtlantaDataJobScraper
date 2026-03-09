import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Scraper",
  description: "Browse data-role job postings",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script defer src="https://cloud.umami.is/script.js" data-website-id="013ecbbf-a644-450f-ada3-0c553ffefd14"></script>
      </head>
      <body>{children}</body>
    </html>
  );
}
