<p>Hello {{ doc.tenant or "Tenant" }},</p>

<p>
  Your rent payment has been received.  
  Please find your receipt details below.
</p>

<table cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 640px;">
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Payment Reference</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.name }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Lease Contract</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.lease_contract }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Airport Code</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.airport_code }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Amount Paid</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.amount_due }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Billing Period</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.period_start }} to {{ doc.period_end }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Status</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.status }}</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd;"><strong>Date Paid</strong></td>
    <td style="border: 1px solid #ddd;">{{ doc.date_paid or "-" }}</td>
  </tr>
</table>

<p style="margin-top: 16px;">
  Thank you.<br>
  Airport Shops Team
</p>