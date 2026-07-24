import { render, screen, fireEvent } from "@testing-library/react";
import UploadDropzone from "@/components/UploadDropzone";

describe("UploadDropzone", () => {
  it("calls onFileSelected when a PDF is chosen via the file input", () => {
    const onFileSelected = jest.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} />);

    const file = new File(["%PDF-1.4"], "contract.pdf", { type: "application/pdf" });
    const input = screen.getByLabelText("Upload PDF") as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelected).toHaveBeenCalledWith(file);
  });

  it("rejects non-PDF files without calling onFileSelected", () => {
    const onFileSelected = jest.fn();
    window.alert = jest.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} />);

    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    const input = screen.getByLabelText("Upload PDF") as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    expect(onFileSelected).not.toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalled();
  });

  it("does not open the file picker or accept drops while disabled", () => {
    const onFileSelected = jest.fn();
    render(<UploadDropzone onFileSelected={onFileSelected} disabled />);

    const dropzone = screen.getByTestId("upload-dropzone");
    const file = new File(["%PDF-1.4"], "contract.pdf", { type: "application/pdf" });

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });

    expect(onFileSelected).not.toHaveBeenCalled();
  });
});
