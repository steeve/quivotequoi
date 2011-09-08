class CreatePeople < ActiveRecord::Migration
  def change
    create_table :people do |t|
      t.string :first_name
      t.string :last_name
      t.date :birth_date
      t.string :birth_place
      t.string :circonscription
      t.string :commission
      t.string :profession
      t.string :personal_url
      t.string :personal_email
      t.string :an_link
      t.integer :hemicycle_place
      t.timestamps
    end
  end
end
