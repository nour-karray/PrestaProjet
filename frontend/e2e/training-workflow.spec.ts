import { expect, test, type APIRequestContext } from "@playwright/test";

const backendUrl = process.env.E2E_BACKEND_URL ?? "http://localhost:8080";
const email = process.env.E2E_ADMIN_EMAIL;
const password = process.env.E2E_ADMIN_PASSWORD;

async function api<T>(
  request: APIRequestContext,
  method: "get" | "post" | "patch",
  path: string,
  data?: object,
  expectedStatus = 200,
): Promise<T> {
  const response = await request[method](`${backendUrl}${path}`, { data });
  expect(response.status(), `${method.toUpperCase()} ${path}: ${await response.text()}`).toBe(
    expectedStatus,
  );
  return (await response.json()) as T;
}

test("parcours réel de la connexion à la clôture", async ({ page }) => {
  test.skip(!email || !password, "E2E_ADMIN_EMAIL et E2E_ADMIN_PASSWORD sont obligatoires.");
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  await page.goto("/connexion");
  await page.getByLabel("Adresse email").fill(email!);
  await page.getByLabel("Mot de passe", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page).toHaveURL(/\/tableau-de-bord$/);
  const request = page.context().request;

  const company = await api<{ id: string }>(
    request,
    "post",
    "/api/companies",
    { name: `E2E Entreprise ${suffix}`, city: "Tunis", country: "Tunisie" },
    201,
  );
  const contact = await api<{ id: string }>(
    request,
    "post",
    `/api/companies/${company.id}/contacts`,
    { full_name: "Contact E2E", is_primary: true },
    201,
  );
  const trainingCase = await api<{ id: string; reference: string }>(
    request,
    "post",
    "/api/training-cases",
    {
      company_id: company.id,
      primary_contact_id: contact.id,
      theme: `Formation E2E ${suffix}`,
    },
    201,
  );
  const trainer = await api<{ id: string }>(
    request,
    "post",
    "/api/trainers",
    { full_name: `Formateur E2E ${suffix}`, daily_rate: "400.000" },
    201,
  );
  await api(request, "post", `/api/training-cases/${trainingCase.id}/trainer`, {
    trainer_id: trainer.id,
  });
  for (const status of [
    "DEMANDE_RECUE",
    "RECHERCHE_FORMATEUR",
    "FORMATEUR_PROPOSE",
    "FORMATEUR_ACCEPTE",
    "BESOIN_A_COMPLETER",
  ]) {
    await api(request, "post", `/api/training-cases/${trainingCase.id}/change-status`, {
      status,
    });
  }

  await api(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/need`,
    {
      target_audience: "Responsables RH",
      location: "Tunis",
      participant_count: 8,
      delivery_mode: "PRESENTIEL",
      duration_hours: 3,
      objectives: "Valider le parcours technique de stabilisation.",
      desired_start_date: "2027-01-15",
      desired_end_date: "2027-01-15",
      constraints: "",
    },
    201,
  );
  await api(request, "post", `/api/training-cases/${trainingCase.id}/need/validate`);

  await api(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/program`,
    {
      title: "Programme de stabilisation",
      general_objectives: "Valider le parcours complet.",
      evaluation_method: "Mise en situation.",
    },
    201,
  );
  const program = await api<{ days: Array<{ id: string }> }>(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/program/days`,
    { title: "Jour 1" },
  );
  await api(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/program/days/${program.days[0].id}/items`,
    {
      item_type: "MODULE",
      title: "Module complet",
      content: "Contenu de validation.",
      theory_minutes: 90,
      practice_minutes: 90,
      methods: ["EXPOSE", "EXERCICE_PRATIQUE"],
    },
  );
  await api(request, "post", `/api/training-cases/${trainingCase.id}/program/submit`);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/program/validate`);

  await api(request, "post", `/api/training-cases/${trainingCase.id}/pricing`, {}, 201);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/pricing/submit`);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/pricing/validate`);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/documents/initialize`);
  const documents = await api<{ all_generated: boolean }>(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/documents/generate-all`,
  );
  expect(documents.all_generated).toBe(true);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/close`);

  await page.goto(`/dossiers/${trainingCase.id}`);
  await expect(page.getByText(trainingCase.reference, { exact: true })).toBeVisible();
  await expect(page.getByText("Terminé", { exact: true })).toBeVisible();
});
