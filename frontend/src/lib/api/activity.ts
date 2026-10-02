import { get, type Query } from "./client.ts";
import { parseActivity, parsePage } from "./parsers.ts";
export const getActivity = (query: Query = {}) => get(["activity"], v => parsePage(v, parseActivity), query);
