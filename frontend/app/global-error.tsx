'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Xatoni log qilish (Sentry yoki boshqa xizmatga yuborish mumkin)
    console.error('Global Error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
          <div className="bg-white p-8 rounded-lg shadow-lg max-w-md text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">
              Tizimda xatolik yuz berdi!
            </h2>
            <p className="text-gray-600 mb-6">
              Kechirasiz, kutilmagan xatolik yuz berdi. Xavfsizlik tizimi ishga tushdi.
            </p>
            <button
              onClick={() => reset()}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Qayta urinib ko'rish
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
