"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLayout } from "@/components/templates";
import { Icon } from "@/components/ui";
import { login } from "@/features/auth/api";
import { ApiError } from "@/lib/api";

const loginSchema = z.object({
  email: z.email("Saisissez une adresse email valide."),
  password: z.string().min(8, "Le mot de passe doit contenir au moins 8 caractères."),
});
type LoginForm = z.infer<typeof loginSchema>;

function LoginVisual() {
  return <div className="auth-visual-content">
    <h2>Apprendre.<br />Évoluer.<br />Réussir.</h2>
    <span className="auth-visual-line" />
    <p>Votre plateforme<br />de formations,<br />partout, tout le temps.</p>
  </div>;
}

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });
  const loginMutation = useMutation({ mutationFn: (values: LoginForm) => login(values.email, values.password), onSuccess: () => router.replace("/tableau-de-bord") });
  const serverError = loginMutation.error instanceof ApiError ? loginMutation.error.message : loginMutation.error ? "Une erreur inattendue est survenue." : null;

  return <AuthLayout visual={<LoginVisual />}>
    <div className="auth-brand"><span><Icon name="book" /></span><strong>Formation <em>Center</em></strong></div>
    <div className="auth-form-wrap">
      <h1>Bienvenue</h1>
      <p>Connectez-vous à votre espace pour continuer.</p>
      <form onSubmit={handleSubmit((values) => loginMutation.mutate(values))} noValidate>
        <label className="auth-field" htmlFor="email">Adresse email<div><Icon name="file" /><input {...register("email")} id="email" type="email" autoComplete="username" placeholder="exemple@entreprise.com" aria-invalid={Boolean(errors.email)} /></div>{errors.email && <small role="alert">{errors.email.message}</small>}</label>
        <label className="auth-field" htmlFor="password">Mot de passe<div><Icon name="settings" /><input {...register("password")} id="password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="Votre mot de passe" aria-invalid={Boolean(errors.password)} /><button type="button" aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"} onClick={() => setShowPassword((value) => !value)}>{showPassword ? "Masquer" : "Afficher"}</button></div>{errors.password && <small role="alert">{errors.password.message}</small>}</label>
        <div className="auth-options"><label><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} /> Se souvenir de moi</label><span>Mot de passe oublié ?</span></div>
        {serverError && <div className="login-error" role="alert"><Icon name="alert" />{serverError}</div>}
        <button type="submit" disabled={loginMutation.isPending} className="login-submit">{loginMutation.isPending ? "Connexion en cours…" : "Se connecter"}</button>
      </form>
      <p className="auth-security">Accès réservé aux utilisateurs autorisés</p>
      <p className="auth-copyright">© {new Date().getFullYear()} Formation Center. Tous droits réservés.</p>
    </div>
  </AuthLayout>;
}
