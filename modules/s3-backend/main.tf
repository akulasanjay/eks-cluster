resource "random_id" "suffix" {
  byte_length = 4
}

module "state_bucket" {
  source      = "../s3"
  bucket_name = "terraform-state-${random_id.suffix.hex}"
  tags        = { Name = "terraform-state-${random_id.suffix.hex}" }
}
