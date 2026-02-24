import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-6xl font-bold text-gray-800 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-gray-600 mb-6">Sahifa topilmadi</h2>
      <p className="text-gray-500 mb-8 text-center max-w-md">
        Siz qidirayotgan sahifa mavjud emas yoki ko'chirilgan bo'lishi mumkin.
      </p>
      <Link 
        href="/"
        className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-md"
      >
        Bosh sahifaga qaytish
      </Link>
    </div>
  );
}
