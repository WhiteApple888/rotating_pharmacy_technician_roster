/*Allows a web browser to read the sheet names (tabs) from an Excel file (.xlsx) directly in the user's browser, 
without sending the file to a server.*/

const CENTRAL_DIRECTORY_SIGNATURE = 0x02014b50 // The start of an entry inside the ZIP's Central Directory (the "Table of Contents").
const END_OF_CENTRAL_DIRECTORY_SIGNATURE = 0x06054b50 // (EOCD) record at the end of the ZIP file.
const LOCAL_FILE_HEADER_SIGNATURE = 0x04034b50 //The start of an individual file's raw data block stored in the archive.

function findEndOfCentralDirectory(bytes: Uint8Array) {
  for (
    let index = bytes.length - 22;
    index >= Math.max(0, bytes.length - 0xffff - 22);
    index--
  ) {
    if (
      new DataView(bytes.buffer, bytes.byteOffset + index, 4).getUint32(
        0,
        true
      ) === END_OF_CENTRAL_DIRECTORY_SIGNATURE
    )
      return index
  }
  throw new Error("The selected file is not a valid XLSX workbook.")
}

async function readZipEntry(bytes: Uint8Array, fileName: string) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  let offset = view.getUint32(findEndOfCentralDirectory(bytes) + 16, true)
  const entries = view.getUint16(findEndOfCentralDirectory(bytes) + 10, true)
  const decoder = new TextDecoder()

  for (let entry = 0; entry < entries; entry++) {
    if (view.getUint32(offset, true) !== CENTRAL_DIRECTORY_SIGNATURE)
      throw new Error("The selected file has an invalid ZIP directory.")
    const compression = view.getUint16(offset + 10, true)
    const compressedSize = view.getUint32(offset + 20, true)
    const nameLength = view.getUint16(offset + 28, true)
    const extraLength = view.getUint16(offset + 30, true)
    const commentLength = view.getUint16(offset + 32, true)
    const localHeaderOffset = view.getUint32(offset + 42, true)
    const name = decoder.decode(
      bytes.subarray(offset + 46, offset + 46 + nameLength)
    )

    if (name === fileName) {
      if (
        view.getUint32(localHeaderOffset, true) !== LOCAL_FILE_HEADER_SIGNATURE
      )
        throw new Error("The selected file has an invalid ZIP entry.")
      const localNameLength = view.getUint16(localHeaderOffset + 26, true)
      const localExtraLength = view.getUint16(localHeaderOffset + 28, true)
      const dataStart =
        localHeaderOffset + 30 + localNameLength + localExtraLength
      const compressed = bytes.slice(dataStart, dataStart + compressedSize)
      if (compression === 0) return compressed
      if (compression === 8) {
        const stream = new Blob([compressed])
          .stream()
          .pipeThrough(
            new DecompressionStream("deflate-raw" as CompressionFormat)
          )
        return new Uint8Array(await new Response(stream).arrayBuffer())
      }
      throw new Error(
        "This XLSX compression format is not supported by your browser."
      )
    }
    offset += 46 + nameLength + extraLength + commentLength
  }
  throw new Error("The selected file is missing workbook metadata.")
}

/** Return the worksheet titles stored in an XLSX file without uploading it. */
export async function getWorksheetNames(file: File) {
  const bytes = new Uint8Array(await file.arrayBuffer())
  const workbookXml = await readZipEntry(bytes, "xl/workbook.xml")
  const document = new DOMParser().parseFromString(
    new TextDecoder().decode(workbookXml),
    "application/xml"
  )
  if (document.querySelector("parsererror"))
    throw new Error("The workbook metadata could not be read.")
  const sheets = Array.from(document.getElementsByTagNameNS("*", "sheet"))
    .map((sheet) => sheet.getAttribute("name"))
    .filter((name): name is string => Boolean(name))
  if (!sheets.length)
    throw new Error("The workbook does not contain any worksheets.")
  return sheets
}
