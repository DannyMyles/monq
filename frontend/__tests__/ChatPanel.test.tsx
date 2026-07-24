import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPanel, { type ChatPanelMessage } from "@/components/ChatPanel";

describe("ChatPanel", () => {
  it("shows the empty state when there are no messages", () => {
    render(<ChatPanel messages={[]} onSend={jest.fn()} />);
    expect(
      screen.getByText("Ask a question about this document to get started.")
    ).toBeInTheDocument();
  });

  it("renders messages and their sources", () => {
    const messages: ChatPanelMessage[] = [
      { role: "user", content: "When is payment due?" },
      {
        role: "assistant",
        content: "Payment is due in 30 days [chunk 1].",
        sources: [{ chunk_index: 1, page_number: 2, snippet: "Payment terms...", score: 0.9 }],
      },
    ];
    render(<ChatPanel messages={messages} onSend={jest.fn()} />);

    expect(screen.getByText("When is payment due?")).toBeInTheDocument();
    expect(screen.getByText("Payment is due in 30 days [chunk 1].")).toBeInTheDocument();
    expect(screen.getByText("Sources (1)")).toBeInTheDocument();
  });

  it("calls onSend with the typed question and clears the input", async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<ChatPanel messages={[]} onSend={onSend} />);

    const input = screen.getByLabelText("Question") as HTMLInputElement;
    await user.type(input, "What is the term length?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).toHaveBeenCalledWith("What is the term length?");
    expect(input.value).toBe("");
  });

  it("disables the send button while sending", () => {
    render(<ChatPanel messages={[]} onSend={jest.fn()} sending />);
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByText("Thinking…")).toBeInTheDocument();
  });
});
