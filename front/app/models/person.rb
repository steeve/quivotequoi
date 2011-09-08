class Person < ActiveRecord::Base
  validates_presence_of :first_name, :last_name, :an_link, :hemicycle_place
end
