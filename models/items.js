'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class items extends Model {
    /**
     * Helper method for defining associations.
     * This method is not a part of Sequelize lifecycle.
     * The `models/index` file will call this method automatically.
     */
    static associate(models) {
      items.belongsTo(models.items, {foreignKey: 'parentID', as: 'parent'});
    }
  };
  items.init({
    anilistID: DataTypes.INTEGER,
    english: DataTypes.STRING,
    romanji: DataTypes.STRING,
    year: DataTypes.INTEGER,
    image: DataTypes.STRING,
    type: DataTypes.STRING,
    parentID: DataTypes.INTEGER
  }, {
    sequelize,
    modelName: 'items',
  });
  return items;
};