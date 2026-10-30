import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
export function ErrorMessage({ message }: { message: string }) {
  return (
    <Alert variant="destructive" className="mt-5" role="alert">
      <AlertTitle>Couldn?t complete the request</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
