class Person < ActiveRecord::Base
  validates_presence_of :first_name, :last_name, :an_link, :hemicycle_place
  has_and_belongs_to_many :groups
end
