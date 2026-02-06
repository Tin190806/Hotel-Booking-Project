HOTEL BOOKING SYSTEM – API SPECIFICATION

Base URL: /api
Data format: JSON
Date format: YYYY-MM-DD (ISO 8601)
Currency: VND

======================================================================

ENDPOINT: GET /rooms

Purpose:
Retrieve list of rooms so users can view and select rooms.

Request:
Method: GET
URL: /api/rooms
Query Parameters (optional):
- room_type: string (single | double | suite)
- capacity: integer

Example:
GET /api/rooms?capacity=2

Response:
Status 200 OK
{
  "rooms": [
    {
      "room_id": "101",
      "room_name": "Deluxe Room",
      "room_type": "double",
      "capacity": 2,
      "price_per_night": 800000,
      "status": "available"
    }
  ]
}

Error:
Status 500 Internal Server Error
{
  "error": "Unable to fetch rooms"
}

======================================================================

ENDPOINT: POST /bookings

Purpose:
Create a new booking for a room.

Request:
Method: POST
URL: /api/bookings
Body (JSON):
{
  "room_id": "101",
  "customer_id": "1",
  "check_in": "2025-01-10",
  "check_out": "2025-01-12"
}

Business Rules:
- check_in must be before check_out
- room must exist and be available
- booking dates must not overlap existing bookings
- customer must exist

Response:
Status 201 Created
{
  "booking_id": "1",
  "room_id": "101",
  "customer_id": "1",
  "check_in": "2025-01-10",
  "check_out": "2025-01-12",
  "final_price": 1600000,
  "status": "confirmed",
  "payment_status": "unpaid",
  "created_at": "2025-01-01T10:00:00"
}

Errors:
Status 400 Bad Request
{
  "error": "Invalid booking dates"
}

Status 404 Not Found
{
  "error": "Room or Customer not found"
}

Status 409 Conflict
{
  "error": "Room is not available for the requested dates"
}

======================================================================

ENDPOINT: DELETE /bookings/{id}

Purpose:
Cancel an existing booking by booking ID.

Request:
Method: DELETE
URL: /api/bookings/{id}

Example:
DELETE /api/bookings/1

Response:
Status 200 OK
{
  "message": "Booking cancelled successfully"
}

Error:
Status 404 Not Found
{
  "error": "Booking not found"
}

Notes:
- Cancel only applies to bookings with status: pending or confirmed
- Canceled bookings are kept for history but marked as status = canceled

======================================================================

END OF API SPECIFICATION
