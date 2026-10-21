package com.baseball.commons.enums;

/**
 * 动作类型枚举
 */
public enum ActionType {
    BATTING("batting", "击球"),
    PITCHING("pitching", "投球");

    private final String code;
    private final String desc;

    ActionType(String code, String desc) {
        this.code = code;
        this.desc = desc;
    }

    public String getCode() {
        return code;
    }

    public String getDesc() {
        return desc;
    }

    public static ActionType fromCode(String code) {
        for (ActionType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }
}