import { expect, test, type APIRequestContext } from "@playwright/test";
import { readFile } from "node:fs/promises";
import path from "node:path";

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
  test.setTimeout(900_000);
  test.skip(!email || !password, "E2E_ADMIN_EMAIL et E2E_ADMIN_PASSWORD sont obligatoires.");
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  await page.goto("/connexion");
  await page.getByLabel("Adresse email").fill(email!);
  await page.getByPlaceholder("Votre mot de passe").fill(password!);
  await page.getByRole("button", { name: "Se connecter" }).click();
  await expect(page).toHaveURL(/\/tableau-de-bord$/, { timeout: 15_000 });
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
  const fixture = await readFile(path.resolve(process.cwd(), "../storage/demo-cv-2-2.pdf"));
  const uploadResponse = await request.post(`${backendUrl}/api/trainer-cvs/upload`, {
    multipart: {
      file: {
        name: `cv-e2e-${suffix}.pdf`,
        mimeType: "application/pdf",
        buffer: Buffer.concat([fixture, Buffer.from(`\n% E2E ${suffix}\n`)]),
      },
    },
  });
  expect(uploadResponse.status(), await uploadResponse.text()).toBe(201);
  const uploadedCv = (await uploadResponse.json()) as { id: string };
  const extractedCv = await api<{
    extraction_status: string;
    parsed_json: Record<string, unknown>;
    extraction_error_code: string | null;
  }>(
    request,
    "post",
    `/api/trainer-cvs/${uploadedCv.id}/extract`,
  );
  expect(extractedCv.extraction_status).toBe("REVIEW_REQUIRED");
  expect(extractedCv.parsed_json).toBeTruthy();
  expect(extractedCv.extraction_error_code).toBeNull();
  const trainer = await api<{ id: string }>(
    request,
    "post",
    `/api/trainer-cvs/${uploadedCv.id}/validate`,
    { full_name: `Formateur E2E ${suffix}`, daily_rate: "400.000" },
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
      level: "BEGINNER",
      location: "Tunis",
      participant_count: 8,
      delivery_mode: "PRESENTIEL",
      duration_hours: 3,
      planned_days_count: 1,
      objectives: "Valider le parcours technique de stabilisation.",
      desired_start_date: "2027-01-15",
      desired_end_date: "2027-01-15",
      constraints: "",
    },
    201,
  );
  await api(request, "post", `/api/training-cases/${trainingCase.id}/need/validate`);

  const generationStartedAt = Date.now();
  const program = await api<{
    days: Array<{
      id: string;
      position: number;
      items: Array<{ position: number; methods: string[]; total_minutes: number }>;
    }>;
    total_minutes: number;
  }>(
    request,
    "post",
    `/api/training-cases/${trainingCase.id}/program/generate-draft`,
  );
  console.log(`E2E_AI_GENERATION_MS=${Date.now() - generationStartedAt}`);
  expect(program.days).toHaveLength(1);
  expect(program.days[0].items.length).toBeGreaterThanOrEqual(2);
  expect(program.total_minutes).toBe(180);
  expect(program.days.map((day) => day.position)).toEqual([1]);
  expect(program.days[0].items.map((item) => item.position)).toEqual(
    program.days[0].items.map((_, index) => index + 1),
  );
  expect(program.days[0].items.reduce((total, item) => total + item.total_minutes, 0)).toBe(180);
  const allowedMethods = new Set([
    "EXPOSE",
    "DEMONSTRATION",
    "EXERCICE_PRATIQUE",
    "ETUDE_DE_CAS",
    "MISE_EN_SITUATION",
    "ECHANGE_COLLECTIF",
    "EVALUATION",
  ]);
  expect(program.days[0].items.every((item) => item.methods.length > 0)).toBe(true);
  expect(program.days[0].items.flatMap((item) => item.methods).every((method) => allowedMethods.has(method))).toBe(true);
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
  const pdf = await request.get(
    `${backendUrl}/api/training-cases/${trainingCase.id}/documents/PROGRAM/download`,
  );
  expect(pdf.status()).toBe(200);
  expect(pdf.headers()["content-type"]).toContain("application/pdf");
  expect((await pdf.body()).length).toBeGreaterThan(100);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/close`);

  const activity = await api<Array<{ action: string }>>(
    request,
    "get",
    `/api/training-cases/${trainingCase.id}/activity`,
  );
  expect(activity.length).toBeGreaterThan(0);
  await api(request, "post", `/api/training-cases/${trainingCase.id}/archive`);
  const archived = await api<{ status: string; is_archived: boolean }>(
    request,
    "get",
    `/api/training-cases/${trainingCase.id}`,
  );
  expect(archived.status).toBe("ARCHIVE");
  expect(archived.is_archived).toBe(true);

  await page.goto(`/dossiers/${trainingCase.id}`);
  await expect(page.getByText(trainingCase.reference, { exact: true })).toBeVisible();
  await expect(page.getByText("Archivé", { exact: true })).toBeVisible();
});
