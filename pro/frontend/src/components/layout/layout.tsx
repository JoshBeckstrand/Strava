import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  const navItems = [
    { label: "Dashboard", to: "/" },
    { label: "Activities", to: "/activities" },
  ];

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary">Strava Pro</h1>
          <p className="text-xs text-gray-500 mt-1">Training Intelligence</p>
        </div>

        <Separator />

        <nav className="flex flex-col p-4 gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "px-4 py-2 rounded-md text-sm font-medium transition-all",
                location.pathname === item.to
                  ? "bg-primary text-white shadow-sm"
                  : "text-gray-700 hover:bg-gray-100"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 p-10 overflow-y-auto">
        {children}
      </main>

    </div>
  );
}
