import { get } from "./client.ts";
import { parseDashboard } from "./parsers.ts";
export const getDashboard = () =>
  get(["dashboard", "statistics"], parseDashboard);
