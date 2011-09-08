class CreateGroups < ActiveRecord::Migration
  def change
    create_table :groups do |t|
      t.string :name
      t.timestamps
    end

    create_table :people_groups do |t|
      t.references :people
      t.references :groups
    end
  end
end
