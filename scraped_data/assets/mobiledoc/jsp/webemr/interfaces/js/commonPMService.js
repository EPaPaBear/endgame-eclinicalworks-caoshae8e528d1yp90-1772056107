const angularModule = angular.module("ecw.service.PMService", []);
let commonServiceFactory = ($http) => {
  const genderList = {
    M: "Male",
    F: "Female",
    U: "Unknown",
    UN: "Undifferentiated",
    O: "Other"
  };
  const defaultHeader = { "Content-Type": "application/json;charset=UTF-8;" };
  let setPromiseService = ({
                             method = "POST",
                             url,
                             data,
                             headers = defaultHeader,
                           }) =>
      $http({
        method: method,
        url: url,
        data: data,
        headers: headers,
      });
  let callBackData = async (promiseObj) => {
    if (typeof promiseObj?.then === "function") {
      try {
        let resData = await promiseObj;
        return [null, resData];
      } catch (error) {
        return [error, null];
      }
    }
  };
  let getObjectValueByKey = (object, key) => {
    let value ="";
    if (object && Object.keys(object).includes(key)) {
      value = object[key];
    }
    return value;
  };
  let getDateFormat = (format, date) => moment(date).format(format);
  return {
    getPromiseService: setPromiseService,
    getGenderList: genderList,
    getDateFormat: getDateFormat,
    getCallbackData: callBackData,
      getObjectValueByKey: getObjectValueByKey,
  };
};
angularModule.factory("commonServiceFactory", commonServiceFactory);
