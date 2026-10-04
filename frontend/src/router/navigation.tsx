import {
  Link as RouterLink,
  useLocation,
  useNavigate,
  useParams as useRouterParams,
  useSearchParams as useRouterSearchParams,
} from "react-router-dom";
import type { ComponentProps } from "react";

export function Link({ href, ...props }: Omit<ComponentProps<typeof RouterLink>, "to"> & { href: string }) {
  return <RouterLink to={href} {...props} />;
}

export function useRouter() {
  const navigate = useNavigate();
  return {
    push: (href: string) => navigate(href),
    replace: (href: string) => navigate(href, { replace: true }),
  };
}

export function usePathname() {
  return useLocation().pathname;
}

export function useParams<T extends Record<string, string>>() {
  return useRouterParams() as T;
}

export function useSearchParams() {
  return useRouterSearchParams()[0];
}

export default Link;
