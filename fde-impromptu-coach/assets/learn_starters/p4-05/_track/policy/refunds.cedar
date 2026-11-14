// Acme Fibre refund policy. YOU fill this in (project 4, step 5).
// A forbid always wins over a permit.

// The support agent may refund up to ₹500 to the customer in the current email.
permit (
    principal == Agent::"acme-support-agent",
    action == Action::"issue_refund",
    resource
)
when { resource.amount_inr <= 500 && resource.customer_id == context.email_customer_id };

// TODO: a billing approver may approve refunds above ₹500
// TODO: forbid any refund to a customer who is not the one in the current email
