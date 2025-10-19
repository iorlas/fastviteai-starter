/**
 * Navigation Component - Top navigation bar for the application
 *
 * Provides global navigation with logo, brand name, and route links.
 * Features responsive design with mobile menu support.
 */

import { Link } from "@tanstack/react-router";
import { useId, useState } from "react";

export function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const logoTitleId = useId();
  const closeIconTitleId = useId();
  const menuIconTitleId = useId();

  return (
    <nav className="sticky top-0 z-50 bg-gradient-to-r from-blue-600 to-indigo-600 shadow-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <Link
              to="/"
              className="flex items-center space-x-3 hover:opacity-90 transition-opacity"
            >
              {/* Logo Icon */}
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 backdrop-blur-sm">
                <svg
                  className="h-6 w-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-labelledby={logoTitleId}
                >
                  <title id={logoTitleId}>Lightning bolt logo</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              {/* Brand Name */}
              <span className="text-xl font-bold text-white">Boilerplate App</span>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex md:items-center md:space-x-1">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/todos">Todos</NavLink>
            <NavLink to="/health">Health Status</NavLink>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center rounded-md p-2 text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white transition-colors"
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? (
                // Close icon
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-labelledby={closeIconTitleId}
                >
                  <title id={closeIconTitleId}>Close menu</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                // Menu icon
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-labelledby={menuIconTitleId}
                >
                  <title id={menuIconTitleId}>Open menu</title>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-white/20">
          <div className="space-y-1 px-2 pb-3 pt-2">
            <MobileNavLink to="/" onClick={() => setMobileMenuOpen(false)}>
              Home
            </MobileNavLink>
            <MobileNavLink to="/todos" onClick={() => setMobileMenuOpen(false)}>
              Todos
            </MobileNavLink>
            <MobileNavLink to="/health" onClick={() => setMobileMenuOpen(false)}>
              Health Status
            </MobileNavLink>
          </div>
        </div>
      )}
    </nav>
  );
}

/**
 * Desktop Navigation Link Component
 */
interface NavLinkProps {
  to: string;
  children: React.ReactNode;
}

function NavLink({ to, children }: NavLinkProps) {
  return (
    <Link
      to={to}
      className="rounded-md px-4 py-2 text-sm font-medium text-white/90 hover:bg-white/10 hover:text-white transition-colors"
      activeProps={{
        className: "bg-white/20 text-white",
      }}
    >
      {children}
    </Link>
  );
}

/**
 * Mobile Navigation Link Component
 */
interface MobileNavLinkProps {
  to: string;
  children: React.ReactNode;
  onClick: () => void;
}

function MobileNavLink({ to, children, onClick }: MobileNavLinkProps) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block rounded-md px-3 py-2 text-base font-medium text-white/90 hover:bg-white/10 hover:text-white transition-colors"
      activeProps={{
        className: "bg-white/20 text-white",
      }}
    >
      {children}
    </Link>
  );
}
