export type ApiErrorKind =
  "unavailable" | "not_found" | "validation" | "unexpected";
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  constructor(kind: ApiErrorKind) {
    super(kind);
    this.name = "ApiError";
    this.kind = kind;
  }
}
export function errorKind(error: unknown): ApiErrorKind {
  return error instanceof ApiError ? error.kind : "unexpected";
}
export function statusError(status: number): ApiError {
  return new ApiError(
    status === 404
      ? "not_found"
      : status === 422 || status === 400
        ? "validation"
        : status === 503 || status === 502 || status === 504
          ? "unavailable"
          : "unexpected",
  );
}
